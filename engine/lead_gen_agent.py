"""
OmniBrain Suite - LeadPulse AI Engine
Autonomous B2B Lead Discovery, Prospect Enrichment & Hyper-Personalized Outreach Generator.
"""

import json
import re
import urllib.request
import urllib.error
import io
import csv

class LeadPulseAgent:
    def __init__(self, api_key: str, model: str = "gemini-3.6-flash"):
        self.api_key = api_key
        self.model = model

    def _call_gemini(self, prompt: str) -> dict:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.3
            }
        }
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                clean_text = re.sub(r"^```(?:json)?\s*", "", text)
                clean_text = re.sub(r"\s*```$", "", clean_text).strip()
                return json.loads(clean_text)
        except Exception as e:
            return {"error": str(e), "leads": []}

    def generate_leads(self, industry: str, location: str, my_service: str, count: int = 5) -> list[dict]:
        prompt = f"""
You are LeadPulse AI, an autonomous B2B Growth & Lead Generation Director.
Generate {count} highly realistic, high-ticket B2B business prospects in:
Industry / Niche: {industry}
Target Geography: {location}
Our Service / Offer to sell them: {my_service}

For each prospect, generate:
1. "company_name": Realistic business name in that city/niche
2. "contact_name": Decision maker name (Founder / Managing Director / Head of Marketing)
3. "title": Exact job title
4. "email": Realistic professional email (e.g. name@company.com)
5. "phone": Realistic localized phone number with country/area code
6. "website": Realistic company website URL
7. "estimated_revenue": Annual revenue estimate (e.g. "$2M - $5M")
8. "primary_pain_point": 1 specific operational/marketing bottleneck they face
9. "personalized_subject": High-converting cold email subject line (<6 words)
10. "personalized_email": 3-paragraph consultative cold pitch highlighting their pain point and our solution
11. "whatsapp_pitch": 2-sentence conversational WhatsApp/SMS outreach message

Return valid JSON with key "leads": array of objects.
"""
        result = self._call_gemini(prompt)
        return result.get("leads", [])

    def export_leads_to_csv(self, leads: list[dict]) -> str:
        output = io.StringIO()
        if not leads:
            return "No leads to export."

        fieldnames = [
            "company_name", "contact_name", "title", "email", "phone",
            "website", "estimated_revenue", "primary_pain_point",
            "personalized_subject", "personalized_email", "whatsapp_pitch"
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for lead in leads:
            writer.writerow(lead)

        return output.getvalue()
