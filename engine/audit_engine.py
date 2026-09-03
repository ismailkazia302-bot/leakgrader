"""
Mastermind AI - Fast 10-Second Business & Revenue Leak Audit Engine
"""

import json
import re
import urllib.request
import urllib.error

class ViralAuditEngine:
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
                "temperature": 0.2,
                "maxOutputTokens": 2048
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
            return {"error": str(e)}

    def audit_business(self, company_or_url: str, industry_hint: str = "") -> dict:
        prompt = f"""
You are the Chief AI Growth Architect at Antigravity Global.
Analyze this company for AI automation readiness and revenue leaks:
Target Company / Domain: {company_or_url}
Industry / Niche: {industry_hint or 'Business / Enterprise'}

Analyze their customer conversion funnel, after-hours lead capture, and automation readiness.
Return strictly valid JSON with:
1. "company_name": Clean company name (e.g. "Stripe Payments" or "LuxeHaven Real Estate")
2. "overall_ai_readiness_score": integer (calculated score between 42 and 86)
3. "estimated_monthly_revenue_leak": calculated estimate string (e.g. "$25,000 - $65,000 / mo")
4. "revenue_leaks": Array of exactly 3 critical bottleneck objects with:
   - "title": Short specific headline
   - "severity": "CRITICAL" | "HIGH" | "MODERATE"
   - "financial_impact": Realistic financial loss description
   - "solution_fix": Exact Antigravity AI agent solution
5. "growth_opportunities": Array of 3 specific growth actions
6. "free_preview_findings": Array of 3 concise preview bullet points
7. "locked_deep_insights": Array of 3 premium insights unlocked upon $9 micro-payment
8. "recommended_agent": "BookFlow 24/7 Sales Closer" | "LeadPulse B2B Engine" | "OmniBrain Document RAG"
"""
        result = self._call_gemini(prompt)
        if "error" not in result:
            result["audit_id"] = f"audit_{hash(company_or_url) % 1000000}"
        return result
