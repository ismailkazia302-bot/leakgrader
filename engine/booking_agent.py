"""
OmniBrain Suite - BookFlow AI Engine
24/7 Conversational AI Sales & Automated Appointment Booking Engine.
Qualifies prospects, handles pricing objections, and books meetings into local CRM ledger.
"""

import json
import time
import urllib.request
import urllib.error

class BookFlowAgent:
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
                "temperature": 0.2
            }
        }
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text)
        except Exception as e:
            return {
                "reply": "Thank you for reaching out! Our team is excited to assist you. Could you share your email and preferred meeting time?",
                "is_qualified": False,
                "booking_details": None
            }

    def chat_and_qualify(self, business_context: str, chat_history: list[dict], user_message: str) -> dict:
        """
        Processes conversational interaction with website visitors, answers questions,
        qualifies budget & need, and extracts structured booking details.
        """
        history_str = ""
        for msg in chat_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            history_str += f"{role.upper()}: {content}\n"

        prompt = f"""
You are BookFlow AI, an elite 24/7 AI Sales Director & Appointment Closer for this business:
---
BUSINESS DETAILS:
{business_context}
---

CONVERSATION HISTORY:
{history_str}
USER: {user_message}

YOUR OBJECTIVES:
1. Provide warm, persuasive, consultative answers about our services, pricing, and capabilities.
2. Ask natural qualifying questions (e.g. project scope, budget range, timeline).
3. If the user expresses interest in a meeting, call, or demo, collect their Name, Email, Phone, Company, and Preferred Date/Time.
4. If they have provided sufficient info (at least name, contact info, and time preference), confirm the appointment enthusiastically.

Return valid JSON with:
1. "reply": String (Your direct conversational message to the user)
2. "is_qualified": Boolean (True if user shared budget/scope)
3. "booking_ready": Boolean (True if name, email/phone, and date/time are present)
4. "extracted_data": Object or null:
   - "client_name": string or null
   - "client_email": string or null
   - "client_phone": string or null
   - "company": string or null
   - "budget_range": string or null
   - "preferred_datetime": string or null
   - "project_notes": string or null
"""
        return self._call_gemini(prompt)
