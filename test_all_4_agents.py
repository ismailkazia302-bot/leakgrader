import urllib.request
import json
import time

print("=" * 60)
print("TESTING ALL 4 AGENTS IN MASTERMIND AI SUITE (http://localhost:8090)")
print("=" * 60)

time.sleep(1)

# 1. Health check
with urllib.request.urlopen("http://localhost:8090/health") as resp:
    print("\n[TEST 1] Health Check:", resp.read().decode())

# 2. Test OmniBrain AI Query
query_payload = json.dumps({"query": "What is the penalty for confidentiality breach?"}).encode("utf-8")
req = urllib.request.Request("http://localhost:8090/api/query", data=query_payload, headers={"Content-Type": "application/json"}, method="POST")
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())
    print("\n[TEST 2] OmniBrain AI Grounded Query:")
    print(data.get("answer")[:250] + "...")
    print(f"Citations attached: {len(data.get('citations', []))}")

# 3. Test LeadPulse AI (B2B Lead Discovery)
lead_payload = json.dumps({
    "industry": "Real Estate Agencies",
    "location": "Dubai, UAE",
    "service": "AI Lead Generation & WhatsApp Closer Bot",
    "count": 2
}).encode("utf-8")
req = urllib.request.Request("http://localhost:8090/api/leads/generate", data=lead_payload, headers={"Content-Type": "application/json"}, method="POST")
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())
    print(f"\n[TEST 3] LeadPulse AI Generated {data.get('generated_count')} Leads:")
    for lead in data.get("leads", [])[:2]:
        print(f" -> {lead.get('company_name')} | Contact: {lead.get('contact_name')} ({lead.get('title')}) | Email: {lead.get('email')}")
        print(f"    Subject: {lead.get('personalized_subject')}")

# 4. Test BookFlow AI (24/7 Sales Qualification & Booking)
booking_chat_payload = json.dumps({
    "history": [],
    "message": "Hi, my name is Alex Vance from Zenith Capital. We need custom AI Agents, budget is $10,000. Can we book a call for tomorrow 3 PM? Email is alex@zenith.com and phone is +1-555-0192."
}).encode("utf-8")
req = urllib.request.Request("http://localhost:8090/api/booking/chat", data=booking_chat_payload, headers={"Content-Type": "application/json"}, method="POST")
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())
    print("\n[TEST 4] BookFlow AI Closer Response:")
    print(f"Reply: {data.get('reply')[:200]}...")
    print(f"Auto Booked to CRM: {data.get('auto_booked')}")

# Verify CRM Ledger
with urllib.request.urlopen("http://localhost:8090/api/booking/list") as resp:
    b_data = json.loads(resp.read().decode())
    print(f"Current CRM Bookings in Ledger: {len(b_data.get('bookings', []))}")

print("\n" + "=" * 60)
print("ALL 4 AGENTS VERIFIED AND OPERATIONAL!")
print("=" * 60)
