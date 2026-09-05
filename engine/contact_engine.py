"""
LeakGrader.com - Inbound Contact & Customer Inquiries Engine
Stores inbound inquiries, partner requests, and enterprise contact forms.
Provides 1-Click Excel / CSV export and JSON storage.
"""

import json
import time
import os
import csv
import io

class ContactEngine:
    def __init__(self, storage_dir: str = None):
        self.storage_dir = storage_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "storage")
        os.makedirs(self.storage_dir, exist_ok=True)
        self.messages_file = os.path.join(self.storage_dir, "contact_messages.json")
        self.messages = self._load_messages()

    def _load_messages(self) -> list:
        if os.path.exists(self.messages_file):
            try:
                with open(self.messages_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_messages(self):
        try:
            with open(self.messages_file, "w", encoding="utf-8") as f:
                json.dump(self.messages, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Error saving contact messages] {e}")

    def save_message(self, name: str, email: str, company: str = "", subject: str = "General Inquiry", message: str = "") -> dict:
        clean_email = (email or "").strip().lower()
        clean_name = (name or "").strip()
        clean_company = (company or "").strip()
        clean_subject = (subject or "").strip() or "General Inquiry"
        clean_message = (message or "").strip()

        if not clean_email or "@" not in clean_email:
            return {"success": False, "error": "Please provide a valid business email address."}
        if not clean_name:
            return {"success": False, "error": "Please provide your full name."}
        if not clean_message:
            return {"success": False, "error": "Please enter your message or inquiry requirements."}

        entry = {
            "id": f"inq_{int(time.time()*1000)}",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "name": clean_name,
            "email": clean_email,
            "company": clean_company,
            "subject": clean_subject,
            "message": clean_message,
            "status": "UNREAD"
        }

        self.messages.insert(0, entry)  # Prepend newest inquiry
        self._save_messages()

        return {
            "success": True,
            "message": "Thank you! Your inquiry has been successfully received. Our growth team will get back to you shortly.",
            "inquiry_id": entry["id"]
        }

    def get_all_messages(self) -> list:
        return self.messages

    def export_csv(self) -> str:
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        writer.writerow(["Inquiry ID", "Timestamp (UTC)", "Full Name", "Email Address", "Company / Website", "Subject / Category", "Message Details", "Status"])
        for m in self.messages:
            writer.writerow([
                m.get("id", ""),
                m.get("timestamp", ""),
                m.get("name", ""),
                m.get("email", ""),
                m.get("company", ""),
                m.get("subject", ""),
                m.get("message", ""),
                m.get("status", "UNREAD")
            ])
        return output.getvalue()
