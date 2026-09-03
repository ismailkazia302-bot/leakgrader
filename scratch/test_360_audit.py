"""
360-Degree Comprehensive Health & Vulnerability Diagnostic Runner (ASCII Safe)
"""

import urllib.request
import urllib.error
import json
import time

BASE_URL = "https://leakgrader.onrender.com"

TESTS = [
    ("Root Landing Page", "GET", f"{BASE_URL}/", None),
    ("Robots.txt Engine", "GET", f"{BASE_URL}/robots.txt", None),
    ("XML Sitemap (37k Pages)", "GET", f"{BASE_URL}/sitemap.xml", None),
    ("Dynamic SVG Badge", "GET", f"{BASE_URL}/badge/stripe.svg", None),
    ("Client Embed Widget.js", "GET", f"{BASE_URL}/widget.js", None),
    ("Instant Audit Scan API", "POST", f"{BASE_URL}/api/audit/scan", {"url_or_company": "airbnb.com"}),
    ("B2B Leads Generator API", "POST", f"{BASE_URL}/api/leads/generate", {"industry": "Real Estate", "location": "Dubai", "count": 2}),
    ("AI Closer Chat API", "POST", f"{BASE_URL}/api/booking/chat", {"business_context": "Test", "message": "Hi", "history": []}),
    ("Checkout Gateway API", "POST", f"{BASE_URL}/api/checkout/create", {"plan_key": "micro_audit"}),
    ("IndexNow Ping API", "POST", f"{BASE_URL}/api/growth/indexnow-ping", {})
]

print("=== STARTING 360-DEGREE MULTI-PILLAR AUDIT ===\n")
for name, method, url, payload in TESTS:
    start = time.time()
    try:
        req = urllib.request.Request(url, headers={"Content-Type": "application/json", "User-Agent": "LeakGrader-Auditor/1.0"})
        data_bytes = json.dumps(payload).encode('utf-8') if payload else None
        with urllib.request.urlopen(req, data=data_bytes, timeout=15) as resp:
            elapsed = int((time.time() - start) * 1000)
            status = resp.status
            content = resp.read()
            print(f"[PASS] {name} -> HTTP {status} ({elapsed}ms) | Size: {len(content):,} bytes")
    except Exception as e:
        elapsed = int((time.time() - start) * 1000)
        print(f"[FAIL] {name} -> Error: {e} ({elapsed}ms)")

print("\n=== AUDIT FINISHED ===")
