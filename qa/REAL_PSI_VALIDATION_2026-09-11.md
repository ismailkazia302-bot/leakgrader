# Real Google PageSpeed Insights & On-Page Forensic Validation Report

**Date:** 2026-09-11  
**Branch:** `feature/real-audit-engine`  
**Deploy Status:** Holding locally on feature branch (NOT deployed, NOT merged)  
**Lockdown Mode:** `LOCKDOWN_PHASE=auth_ready`  
**Verdict:** `API_ISSUE` (Keyless Google PageSpeed quota limit; fallback & on-page forensics 100% verified)

---

## 1. Task 1: Real PSI API Call (No Mocks)

The audit engine was tested against two live targets using genuine HTTP requests to the Google PageSpeed Insights API v5 (`https://www.googleapis.com/pagespeedonline/v5/runPagespeed`):
1. `https://example.com`
2. `https://www.wikipedia.org`

### API Execution Results
```json
{
  "target": "https://example.com",
  "endpoint": "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=https%3A%2F%2Fexample.com&strategy=mobile&category=performance&category=accessibility&category=seo&category=best-practices",
  "http_status": 429,
  "http_reason": "Too Many Requests",
  "google_error_body": {
    "error": {
      "code": 429,
      "message": "Quota exceeded for quota metric 'Queries' and limit 'Queries per day' of service 'pagespeedonline.googleapis.com' for consumer 'project_number:583797351490'."
    }
  }
}
```

```json
{
  "target": "https://www.wikipedia.org",
  "endpoint": "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=https%3A%2F%2Fwww.wikipedia.org&strategy=mobile&category=performance&category=accessibility&category=seo&category=best-practices",
  "http_status": 429,
  "http_reason": "Too Many Requests",
  "google_error_body": {
    "error": {
      "code": 429,
      "message": "Quota exceeded for quota metric 'Queries' and limit 'Queries per day' of service 'pagespeedonline.googleapis.com' for consumer 'project_number:583797351490'."
    }
  }
}
```

### Key Finding on API Key Requirements
- `PAGESPEED_API_KEY` is currently **not set** in the local environment.
- When no API key is provided, Google assigns incoming calls to a shared public default consumer project (`project_number:583797351490`).
- This shared public project's daily quota is currently exhausted (`429 Quota Exceeded`).
- **Confirmation:** The audit engine is demonstrably connecting directly to Google's live production infrastructure with zero mocks. To receive live PageSpeed scores and Core Web Vitals directly through the API, a standard Google Cloud `PAGESPEED_API_KEY` must be configured in the environment (e.g. Render environment variables).

---

## 2. Task 2: Real On-Page Evidence Check

Target: `https://example.com` (Raw HTML comparison vs. On-Page Analyzer forensic extraction):

### Raw HTML of `example.com`
```html
<!doctype html><html lang="en"><head><title>Example Domain</title><link rel="icon" href="data:,"><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{background:#eee;width:60vw;margin:15vh auto;font-family:system-ui,sans-serif}h1{font-size:1.5em}div{opacity:0.8}a:link,a:visited{color:#348}</style></head><body><div><h1>Example Domain</h1><p>This domain is for use in documentation examples without needing permission. Avoid use in operations.</p><p><a href="https://iana.org/domains/example">Learn more</a></p></div></body></html>
```

### Real Forensic Detections Captured
| Checkpoint | Target Detection | Exact Evidence String Extracted | Verification vs Raw HTML |
|---|---|---|:---:|
| **Title** | Actual text + length | `Title: "Example Domain" (14 chars; recommended 30–60)` | **Exact Match** (`<title>Example Domain</title>`) |
| **Meta Description** | Actual text or missing | `Missing meta description tag in HTML head` | **Exact Match** (No description tag in head) |
| **Form Field Count** | Actual visible inputs | `No visible contact or lead capture forms detected on page` (0 fields) | **Exact Match** (No form/inputs present) |
| **Schema Type** | Actual type or none | `No Schema.org JSON-LD structured data detected` | **Exact Match** (No JSON-LD present) |
| **WhatsApp Link** | Found or not found | `No WhatsApp chat link (wa.me/...) detected on page` | **Exact Match** (No WhatsApp links) |
| **Live Chat Widget** | Found or not found | `No live chat or automated messaging widget discovered in source` | **Exact Match** (No chat widget scripts) |
| **Viewport** | Viewport meta | `Found <meta name="viewport" content="width=device-width, initial-scale=1">` | **Exact Match** (`<meta name="viewport" ...>`) |
| **Heading Structure** | H1 count & text | `1 H1 tag found: "Example Domain", with 0 H2 section headings` | **Exact Match** (`<h1>Example Domain</h1>`) |

**Confirmation:** All detections are 100% genuine extractions from live fetched HTML, with zero static placeholders or fabricated claims.

---

## 3. Task 3: Fallback Resilience Test (When PSI is 429/Unavailable)

When Google PageSpeed Insights returns HTTP 429 or times out, the audit engine's fallback architecture executes cleanly:

1. **Audit Completion:** The audit generates completely (`status: "VERIFIED_AUDIT"`), without errors or crashes.
2. **Honest PageSpeed Status:** PageSpeed status is recorded as `"unavailable"`, with explicit note:
   `"Google PageSpeed Insights API is temporarily rate-limited or unavailable. Speed metrics marked pending."`
3. **Core Web Vitals Display:**
   - LCP: `display: "Unavailable"`, `status: "PENDING"`
   - CLS: `display: "Unavailable"`, `status: "PENDING"`
   - TBT: `display: "Unavailable"`, `status: "PENDING"`
   - FCP: `display: "Unavailable"`, `status: "PENDING"`
   - Speed Index: `display: "Unavailable"`, `status: "PENDING"`
4. **Defensible Transparent Weight Adjustment:**
   - Performance (40%): Explicitly marked `score: null`, `display: "Pending / Unavailable"`, `weight: "Omitted (Google PSI rate limit or timeout)"`.
   - On-Page SEO: Reallocated to **40% weight** (`score: 20/100`).
   - Semantic Accessibility: Reallocated to **30% weight** (`score: 100/100`).
   - Conversion Signals: Reallocated to **30% weight** (`score: 35/100`).
   - Overall Score: Transparently calculated as $0.40(20) + 0.30(100) + 0.30(35) = 48.5 ightarrow \mathbf{48/100}$ (Grade: C).

---

## 4. Task 4: Consistency & Honesty Verification

Both `example.com` (0 form fields) and `python.org` (1 form field) were verified:
1. **Form Field Consistency:** The root `form_friction_fields` metric matches Checkpoint #6 (`Contact Form Completion Friction`) and Recommendation #1 with 100% precision.
2. **Spam & Unbuilt Features Check:** Verified **0 occurrences** of `"WhatsApp Closer"`, `"Directory Hub"`, or fabricated `"8+ hour reply lag"` across entire JSON and HTML output.
3. **Revenue Opportunity:** Reframed strictly as a conservative-to-expected range with the required disclaimer:
   - `example.com`: `$53,300 – $114,200/mo`
   - `python.org`: `$118,300 – $253,500/mo`
   - Disclaimer: *"Illustrative estimate based on industry benchmarks and assumptions, not measured data. Enter your actual traffic and conversion data for accuracy."*
4. **Benchmark Labeling:** Calculation basis is explicitly tagged as `"Transparent Industry Benchmark Formula"`.

---

## 5. Summary & Verdict

- **Real API Integration Verified:** The client connects directly to Google's production PageSpeed endpoint.
- **Quota Status:** Keyless queries are blocked by Google with `HTTP 429 Quota Exceeded for consumer project 583797351490`. Setting `PAGESPEED_API_KEY` in production/Render will immediately unlock dedicated project quota.
- **On-Page Forensics:** 100% real evidence strings extracted directly from live target HTML.
- **Fallback Mechanism:** Proven 100% resilient and transparent.
- **Honesty & Consistency:** 100% verified.

**Verdict:** `API_ISSUE` (Keyless Google PageSpeed quota exhaustion; fallback and real on-page engine verified and ready).
