"""
LeakGrader.com - Email Capture, User Signup & Lead Vault Engine
Stores subscriber emails, saved company audit alerts, and generates CSV exports.
"""

import json
import time
import os

class EmailVaultEngine:
    def __init__(self, storage_dir: str = None):
        self.storage_dir = storage_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "storage")
        os.makedirs(self.storage_dir, exist_ok=True)
        self.vault_file = os.path.join(self.storage_dir, "subscribers_vault.json")
        self.subscribers = self._load_vault()

    def _load_vault(self) -> list:
        if os.path.exists(self.vault_file):
            try:
                with open(self.vault_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_vault(self):
        try:
            with open(self.vault_file, "w", encoding="utf-8") as f:
                json.dump(self.subscribers, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Error saving subscribers vault] {e}")

    def capture_subscriber(self, email: str, company: str = "", source: str = "audit_report") -> dict:
        clean_email = email.strip().lower()
        if not clean_email or "@" not in clean_email:
            return {"success": False, "error": "Invalid email address format"}

        # Check existing
        for s in self.subscribers:
            if s.get("email") == clean_email:
                if company and company not in s.get("audited_companies", []):
                    s.setdefault("audited_companies", []).append(company)
                    self._save_vault()
                return {
                    "success": True,
                    "is_new": False,
                    "message": "Welcome back! Audit report sent to your inbox.",
                    "subscriber": s
                }

        entry = {
            "id": f"sub_{int(time.time()*1000)}",
            "email": clean_email,
            "audited_companies": [company] if company else [],
            "source": source,
            "subscribed_at": time.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "weekly_alerts_enabled": True
        }

        self.subscribers.append(entry)
        self._save_vault()

        return {
            "success": True,
            "is_new": True,
            "message": "Successfully subscribed! Full PDF dossier sent to your email.",
            "subscriber": entry
        }

    def get_all_subscribers(self) -> list:
        return self.subscribers

    def export_csv(self) -> str:
        lines = ["Subscriber ID,Email,Audited Companies,Subscribed At,Source"]
        for s in self.subscribers:
            companies = "; ".join(s.get("audited_companies", []))
            lines.append(f'"{s.get("id")}","{s.get("email")}","{companies}","{s.get("subscribed_at")}","{s.get("source")}"')
        return "\n".join(lines)
