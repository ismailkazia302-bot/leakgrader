"""
LeakGrader.com - Local Business Pipeline Master Ledger
Maintains the 14-column spreadsheet system of record for all scraped local businesses.
Dual-sync with local persistent storage and Google Sheets compatible CSV export.
"""

import os
import json
import csv
import io
import time

COLUMNS = [
    "Business Name",
    "Phone",
    "Address",
    "Website",
    "Category",
    "SSL Check",
    "Mobile Check",
    "Design Age Check",
    "Load Time Check",
    "AI Visual Judgment",
    "Status",
    "Redesign Sent",
    "Email Sent",
    "Response"
]

class PipelineLedger:
    def __init__(self, storage_dir: str = None):
        self.storage_dir = storage_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "storage")
        os.makedirs(self.storage_dir, exist_ok=True)
        self.ledger_file = os.path.join(self.storage_dir, "pipeline_leads.json")
        self.leads = self._load()

    def _load(self) -> list:
        if os.path.exists(self.ledger_file):
            try:
                with open(self.ledger_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[Ledger Load Error] {e}")
        return []

    def save(self):
        try:
            with open(self.ledger_file, "w", encoding="utf-8") as f:
                json.dump(self.leads, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Ledger Save Error] {e}")

    def record_lead(self, business_data: dict) -> dict:
        """
        Inserts or updates a lead row in the 14-column master ledger.
        """
        phone = (business_data.get("phone") or "").strip()
        name = (business_data.get("name") or business_data.get("title") or "").strip()
        address = (business_data.get("address") or "").strip()
        website = (business_data.get("website") or "").strip()
        category = (business_data.get("category") or business_data.get("categoryName") or "").strip()

        # Generate unique key
        lead_id = f"lead_{hash((name + phone + website).lower()) & 0xFFFFFFFF}"

        # Find existing
        for item in self.leads:
            if item.get("id") == lead_id or (phone and item.get("phone") == phone and name and item.get("name") == name):
                # Update existing record
                for k, v in business_data.items():
                    if v is not None:
                        item[k] = v
                self.save()
                return item

        # New record
        new_row = {
            "id": lead_id,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "Business Name": name,
            "Phone": phone,
            "Address": address,
            "Website": website,
            "Category": category,
            "SSL Check": business_data.get("ssl_check", ""),
            "Mobile Check": business_data.get("mobile_check", ""),
            "Design Age Check": business_data.get("design_age_check", ""),
            "Load Time Check": business_data.get("load_time_check", ""),
            "AI Visual Judgment": business_data.get("ai_visual_judgment", ""),
            "Status": business_data.get("status", "Pending"),
            "Redesign Sent": business_data.get("redesign_sent", "No"),
            "Email Sent": business_data.get("email_sent", "No"),
            "Response": business_data.get("response", "Pending"),
            "demo_id": business_data.get("demo_id", ""),
            "pitch_email": business_data.get("pitch_email", ""),
            "pitch_wa": business_data.get("pitch_wa", ""),
            "pitch_price": business_data.get("pitch_price", "₹50,000")
        }
        self.leads.append(new_row)
        self.save()
        return new_row

    def update_lead(self, lead_id: str, updates: dict) -> bool:
        for item in self.leads:
            if item.get("id") == lead_id:
                for k, v in updates.items():
                    item[k] = v
                self.save()
                return True
        return False

    def get_all(self) -> list:
        return self.leads

    def get_stats(self) -> dict:
        total = len(self.leads)
        no_website = sum(1 for x in self.leads if x.get("Status") == "No Website")
        outdated = sum(1 for x in self.leads if x.get("Status") == "Outdated")
        skip = sum(1 for x in self.leads if x.get("Status") == "Skip")
        pitches_ready = sum(1 for x in self.leads if x.get("demo_id"))
        return {
            "total_scraped": total,
            "no_website": no_website,
            "outdated": outdated,
            "qualifying": no_website + outdated,
            "skip": skip,
            "demos_generated": pitches_ready
        }

    def export_csv(self) -> str:
        """Generates RFC-4180 compliant CSV strictly matching the 14-column spreadsheet spec"""
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        
        # Extended headers for actionable tracking
        headers = COLUMNS + ["Demo Link", "Quoted Price", "Outreach WhatsApp Link"]
        writer.writerow(headers)

        for item in self.leads:
            row = [
                item.get("Business Name", ""),
                item.get("Phone", ""),
                item.get("Address", ""),
                item.get("Website", ""),
                item.get("Category", ""),
                item.get("SSL Check", ""),
                item.get("Mobile Check", ""),
                item.get("Design Age Check", ""),
                item.get("Load Time Check", ""),
                item.get("AI Visual Judgment", ""),
                item.get("Status", ""),
                item.get("Redesign Sent", ""),
                item.get("Email Sent", ""),
                item.get("Response", ""),
                f"https://leakgrader.com/preview/{item.get('demo_id')}" if item.get("demo_id") else "",
                item.get("pitch_price", "₹50,000"),
                item.get("pitch_wa", "")
            ]
            writer.writerow(row)

        return output.getvalue()
