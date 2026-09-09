# Architectural Assessment: File-Backed Storage & Multi-Process Safety
**Date:** September 7, 2026  
**Auditor:** Senior QA Engineer  
**Component:** Platform Data Persistence Layer  
**Verdict:** ⛔ **PRODUCTION RELEASE BLOCKED (Migrate to Managed Database)**  

---

## 1. Scope of File-Backed Storage Audit

The platform currently relies on JSON files persisted on local disk within `omnibrain/storage/`:
1. `active_entitlements.json`: Active customer tokens, subscribed plans, expiration dates, and tenant refs.
2. `processed_webhook_events.json`: Replay protection ledger and idempotency records for Lemon Squeezy webhooks.
3. `leads_vault.json`: Generated B2B decision-maker records.
4. `appointments.json`: BookFlow AI closer consultations and bookings.
5. `audits_vault.json`: Public audit scan records and diagnostic scores.
6. `knowledge_index.json`: OmniBrain RAG document metadata and text chunks.
7. `email_vault.json`: Captured subscriber emails and company leads.
8. `pipeline_leads.json`: GMB and local outreach lead ledger.

---

## 2. Technical Evaluation: Concurrency & Mutex Locking

### Existing Safeguard
In `engine/security_guard.py`, atomic persistence is implemented via:
```python
def _atomic_json_dump(filepath: str, data: dict):
    dir_name = os.path.dirname(filepath)
    os.makedirs(dir_name, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8") as tf:
        json.dump(data, tf, indent=2, ensure_ascii=False)
        temp_name = tf.name
    os.replace(temp_name, filepath)
```
Protected by:
```python
_SECURITY_LOCK = threading.RLock()
```

### Why This Is Valid for Staging / Single-Process
1. **Zero Truncation:** Writing to a temporary file in the same directory and utilizing `os.replace` guarantees an atomic inode swap on POSIX filesystems and atomic rename on NTFS. Process termination or crash during write cannot corrupt the target JSON file.
2. **Intra-Process Thread Safety:** `threading.RLock()` ensures that concurrent threads in Python's default `ThreadingHTTPServer` cannot interleave writes or read partially written state.

### Why This Fails in Production (Multi-Worker & Ephemeral Cloud)

#### Reason 1: Multi-Process Non-Synchronization
- In standard production configurations (e.g. Gunicorn with 4-8 Uvicorn/WSGI workers, or multiple container replicas behind a load balancer), each worker runs in an independent OS process with its own private virtual memory space.
- A Python `threading.Lock` exists strictly within the heap of a single process. **Process A cannot see or respect Process B's lock.**
- If two webhooks arrive simultaneously and are routed to different worker processes:
  1. Worker A and Worker B read `processed_webhook_events.json` at the same instant.
  2. Both see `evt_123` as unprocessed.
  3. Both process the event and issue duplicate tokens.
  4. Both write temporary files and execute `os.replace`.
  5. The last worker to call `os.replace` overwrites the first worker's state, leading to **silent lost updates**.

#### Reason 2: Ephemeral Filesystem Data Loss (Render Cloud)
- Render web services run on containerized infrastructure with **ephemeral root filesystems**.
- Any of the following standard operational events will destroy the local disk and revert to the Git commit state:
  - Application restart due to memory threshold or platform health check.
  - Zero-downtime deployment of any code change.
  - Server migration to a new physical host.
  - Render free tier instance sleep/wake cycle.
- **Consequences for LeakGrader:**
  - **Customer Lockout:** Paying customers who purchased subscriptions will have their entitlement record in `active_entitlements.json` deleted. Their bearer tokens will immediately return HTTP 401 Unrecognized Token.
  - **Webhook Replay Vulnerability:** `processed_webhook_events.json` will be wiped, allowing re-delivery of historic webhooks to grant duplicate tokens or corrupt state.
  - **CRM Loss:** All booked appointments in `appointments.json` and generated leads in `leads_vault.json` will vanish.

---

## 3. Mandatory Remediation for Production Release

To lift the `RELEASE_BLOCKED` verdict, the engineering team must implement the following database architecture:

```
                                 ┌─────────────────────────┐
                                 │   Managed PostgreSQL    │
                                 │   (Render / AWS RDS)    │
                                 └────────────┬────────────┘
                                              │
                      ┌───────────────────────┴───────────────────────┐
                      │                                               │
             ┌────────▼────────┐                             ┌────────▼────────┐
             │ active_         │                             │ processed_      │
             │ entitlements    │                             │ webhook_events  │
             ├─────────────────┤                             ├─────────────────┤
             │ token (PK)      │                             │ event_id (PK)   │
             │ order_id (UQ)   │                             │ event_name      │
             │ customer_ref    │                             │ processed_at    │
             │ plan            │                             │ token_created   │
             │ status          │                             │ payload_hash    │
             │ expires_at      │                             └─────────────────┘
             └─────────────────┘
```

1. **Relational Constraints:**
   - `token` as Primary Key (Indexed UUID).
   - `order_id` as Unique Index (prevents duplicate entitlement generation across processes).
   - `event_id` as Primary Key in `processed_webhook_events` (guarantees DB-level idempotency rejection).
2. **ACID Transactions:**
   - Webhook processing wrapped in `BEGIN ... COMMIT` with `SELECT ... FOR UPDATE` row-level locking.
3. **Persistent Volume Alternative (Interim Staging Only):**
   - If deploying to Render Staging prior to full database migration, mount a persistent disk volume to `/var/data` and point `STORAGE_DIR` to the mounted volume.\n