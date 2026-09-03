import json
import urllib.request
import urllib.parse
import time

BASE_URL = "http://localhost:8090"

def test_endpoint(name, method, path, data=None):
    print(f"\n==================================================")
    print(f"TESTING: {name} [{method} {path}]")
    print(f"==================================================")
    
    url = BASE_URL + path
    headers = {"Content-Type": "application/json"}
    
    try:
        req_data = json.dumps(data).encode("utf-8") if data else None
        req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
        
        start_time = time.time()
        with urllib.request.urlopen(req, timeout=30) as resp:
            elapsed = time.time() - start_time
            status_code = resp.getcode()
            body = resp.read().decode("utf-8")
            
            print(f" STATUS: {status_code} | ELAPSED: {elapsed:.2f}s")
            
            try:
                parsed = json.loads(body)
                print(" RESPONSE SAMPLE:")
                print(json.dumps(parsed, indent=2)[:500] + "\n...(truncated)")
                return True, parsed
            except Exception:
                print(f" RAW BODY (first 200 chars): {body[:200]}")
                return True, body
    except Exception as e:
        print(f" FAILED: {str(e)}")
        return False, str(e)

def run_all_tests():
    print("\n[STARTING COMPREHENSIVE LIVE SYSTEM AUDIT...]\n")
    results = {}

    # 1. Test 10s Viral Website Audit
    ok, res = test_endpoint(
        name="1. Viral Website AI Audit Engine",
        method="POST",
        path="/api/audit/run",
        data={"url_or_company": "https://stripe.com"}
    )
    results["1. Viral Audit"] = ok and "audit" in res and res["audit"].get("overall_ai_readiness_score") is not None

    # 2. Test B2B LeadPulse Prospect Generation
    ok, res = test_endpoint(
        name="2. B2B Prospect Generator & Pitch AI",
        method="POST",
        path="/api/leads/generate",
        data={
            "industry": "Private Dental Clinics",
            "location": "London, UK",
            "service": "24/7 AI WhatsApp Patient Booking Bot",
            "count": 3
        }
    )
    results["2. B2B Prospecting"] = ok and len(res.get("leads", [])) >= 3

    # 3. Test 24/7 AI Closer Chat & Auto-Booking
    ok, res = test_endpoint(
        name="3. 24/7 AI Sales Closer Bot",
        method="POST",
        path="/api/booking/chat",
        data={
            "history": [],
            "message": "Hi, I am Dr. James from Harley Dental London. I want to deploy your 24/7 WhatsApp AI Closer for $1,500 setup. Can we book a call for tomorrow at 4 PM?"
        }
    )
    results["3. AI Closer Bot"] = ok and "reply" in res

    # 4. Test OmniBrain Query (Second Brain)
    ok, res = test_endpoint(
        name="4. Document Second Brain Query",
        method="POST",
        path="/api/query",
        data={"query": "What is the key advantage of an automated WhatsApp Closer over human SDRs?"}
    )
    results["4. OmniBrain QA"] = ok and "answer" in res

    # 5. Test ContentCrew SEO Article Generation
    ok, res = test_endpoint(
        name="5. ContentCrew Multi-Agent SEO Article Sprint",
        method="POST",
        path="/api/content-crew/run",
        data={
            "topic": "Why Dental Clinics are Losing 35% of Revenue Without 24/7 WhatsApp AI",
            "audience": "Clinic Owners & Practice Managers",
            "tone": "Authoritative & Results-Driven"
        }
    )
    results["5. ContentCrew SEO"] = ok and "data" in res and res["data"].get("full_article_markdown") is not None

    # 6. Test Programmatic SEO Directory & Sitemap
    ok, res = test_endpoint(
        name="6. Programmatic 10k SEO Directory",
        method="GET",
        path="/api/seo/directory"
    )
    results["6. Programmatic SEO"] = ok and len(res.get("pages", [])) > 0

    # 7. Test Micro-Checkout ($9 Full Audit Report)
    ok, res = test_endpoint(
        name="7. Micro-Checkout Monetization",
        method="POST",
        path="/api/checkout/create",
        data={"plan_key": "micro_audit", "email": "doctor@harleydental.co.uk"}
    )
    results["7. Monetization Checkout"] = ok and res.get("order", {}).get("status") == "COMPLETED"

    print("\n" + "="*50)
    print("FINAL TEST REPORT SUMMARY:")
    print("="*50)
    for feature, passed in results.items():
        status = "[PASSED]" if passed else "[FAILED]"
        print(f"{feature:<40} : {status}")
    print("="*50)

if __name__ == "__main__":
    run_all_tests()
