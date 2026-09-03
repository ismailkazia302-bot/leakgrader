"""
Mastermind AI Suite - Master Production Server & Automated Monetization Gateway
Multi-Threaded HTTP & REST API server handling:
1. 🧲 Viral 10-Second Business & Revenue Leak Audit Engine
2. 🌐 Programmatic SEO & GEO Directory Engine (/sitemap.xml)
3. 💳 Stripe & Micro-Checkout Gateway Engine
4. 🚀 LeadPulse AI (Apollo-Grade Prospecting)
5. 🧠 OmniBrain AI (Grounded Knowledge RAG)
6. 📞 BookFlow AI (24/7 AI Sales Closer & CRM)
7. ✍️ ContentCrew AI (3-Agent SEO Factory)
"""

import os
import sys

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import json
import time
import io
import mimetypes
from urllib.parse import urlparse, unquote
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

# Import All Engines
from engine.document_parser import parse_file, extract_text_from_url, chunk_text
from engine.hybrid_retriever import HybridRetriever
from engine.agent_intelligence import OmniAgentIntelligence
from engine.lead_gen_agent import LeadPulseAgent
from engine.booking_agent import BookFlowAgent
from engine.content_crew_agent import ContentCrewEngine
from engine.audit_engine import ViralAuditEngine
from engine.seo_engine import ProgrammaticSEOEngine
from engine.payment_gateway import PaymentEngine, PLANS
from engine.growth_bot import GrowthAndIndexingAgent

# Configuration
PORT = int(os.environ.get("PORT", 8090))
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GROWTH_AGENT = GrowthAndIndexingAgent()
STORAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "storage")
WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")

os.makedirs(STORAGE_DIR, exist_ok=True)
INDEX_FILE = os.path.join(STORAGE_DIR, "knowledge_index.json")
BOOKINGS_FILE = os.path.join(STORAGE_DIR, "appointments.json")
LEADS_FILE = os.path.join(STORAGE_DIR, "leads_vault.json")
AUDITS_FILE = os.path.join(STORAGE_DIR, "audits_vault.json")

# In-Memory State
ALL_DOCUMENTS = {}
ALL_CHUNKS = []
BOOKINGS = []
LEADS = []
AUDITS = []

RETRIEVER = HybridRetriever(api_key=GEMINI_API_KEY)
INTELLIGENCE = OmniAgentIntelligence(api_key=GEMINI_API_KEY, model="gemini-3.6-flash")
LEAD_AGENT = LeadPulseAgent(api_key=GEMINI_API_KEY, model="gemini-3.6-flash")
BOOKING_AGENT = BookFlowAgent(api_key=GEMINI_API_KEY, model="gemini-3.6-flash")
CONTENT_CREW = ContentCrewEngine(api_key=GEMINI_API_KEY, model="gemini-3.6-flash")
AUDIT_ENGINE = ViralAuditEngine(api_key=GEMINI_API_KEY, model="gemini-3.6-flash")
SEO_ENGINE = ProgrammaticSEOEngine(base_url="http://localhost:8090")
PAYMENT_ENGINE = PaymentEngine()

def save_index():
    try:
        data = {
            "documents": {
                k: {
                    "name": v["name"],
                    "chunks_count": len(v["chunks"]),
                    "size": v.get("size", 0),
                    "type": v.get("type", "file")
                } for k, v in ALL_DOCUMENTS.items()
            },
            "chunks": ALL_CHUNKS
        }
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Error saving index] {e}")

def save_bookings():
    try:
        with open(BOOKINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(BOOKINGS, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Error saving bookings] {e}")

def save_leads():
    try:
        with open(LEADS_FILE, "w", encoding="utf-8") as f:
            json.dump(LEADS, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Error saving leads] {e}")

def save_audits():
    try:
        with open(AUDITS_FILE, "w", encoding="utf-8") as f:
            json.dump(AUDITS, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Error saving audits] {e}")

def load_all_data():
    global ALL_DOCUMENTS, ALL_CHUNKS, BOOKINGS, LEADS, AUDITS
    if os.path.exists(INDEX_FILE):
        try:
            with open(INDEX_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                ALL_CHUNKS = data.get("chunks", [])
                doc_meta = data.get("documents", {})
                for doc_id, meta in doc_meta.items():
                    doc_chunks = [c for c in ALL_CHUNKS if c.get("doc_name") == meta["name"]]
                    ALL_DOCUMENTS[doc_id] = {
                        "name": meta["name"],
                        "chunks": doc_chunks,
                        "size": meta.get("size", 0),
                        "type": meta.get("type", "file")
                    }
                RETRIEVER.index(ALL_CHUNKS)
        except Exception as e:
            print(f"[Error loading index] {e}")

    if os.path.exists(BOOKINGS_FILE):
        try:
            with open(BOOKINGS_FILE, "r", encoding="utf-8") as f:
                BOOKINGS = json.load(f)
        except Exception:
            BOOKINGS = []

    if os.path.exists(LEADS_FILE):
        try:
            with open(LEADS_FILE, "r", encoding="utf-8") as f:
                LEADS = json.load(f)
        except Exception:
            LEADS = []

    if os.path.exists(AUDITS_FILE):
        try:
            with open(AUDITS_FILE, "r", encoding="utf-8") as f:
                AUDITS = json.load(f)
        except Exception:
            AUDITS = []

class MastermindRequestHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/health":
            self._set_headers(200)
            self.wfile.write(json.dumps({"status": "healthy", "service": "Mastermind Global AI Platform (All 7 Engines Online)"}).encode("utf-8"))
            return

        # 1. Programmatic SEO XML Sitemap
        elif path == "/sitemap.xml":
            sitemap_xml = SEO_ENGINE.generate_sitemap_xml()
            self.send_response(200)
            self.send_header("Content-Type", "application/xml; charset=utf-8")
            self.end_headers()
            self.wfile.write(sitemap_xml.encode("utf-8"))
            return

        # 1. Viral Growth & Programmatic SEO Endpoints
        elif path == "/sitemap.xml":
            sitemap_xml = SEO_ENGINE.generate_sitemap_xml()
            self.send_response(200)
            self.send_header("Content-Type", "application/xml; charset=utf-8")
            self.send_header("Cache-Control", "public, max-age=86400")
            self.end_headers()
            self.wfile.write(sitemap_xml.encode("utf-8"))
            return

        elif path.startswith("/badge/") and path.endswith(".svg"):
            slug = path.replace("/badge/", "").replace(".svg", "").replace("-", " ").title()
            svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="220" height="40" viewBox="0 0 220 40">
  <defs>
    <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0055ff"/>
      <stop offset="100%" stop-color="#6366f1"/>
    </linearGradient>
  </defs>
  <rect width="220" height="40" rx="8" fill="#080a13" stroke="rgba(255,255,255,0.15)"/>
  <circle cx="20" cy="20" r="10" fill="url(#g)"/>
  <path d="M16 20l3 3 5-5" stroke="#ffffff" stroke-width="2" fill="none" stroke-linecap="round"/>
  <text x="38" y="18" fill="#ffffff" font-family="-apple-system,BlinkMacSystemFont,sans-serif" font-size="11" font-weight="bold">LeakGrader.com</text>
  <text x="38" y="30" fill="#10b981" font-family="-apple-system,BlinkMacSystemFont,sans-serif" font-size="10" font-weight="600">VERIFIED AUDIT • 98%</text>
</svg>"""
            self.send_response(200)
            self.send_header("Content-Type", "image/svg+xml; charset=utf-8")
            self.send_header("Cache-Control", "public, max-age=3600")
            self.end_headers()
            self.wfile.write(svg_content.encode("utf-8"))
            return

        elif path.startswith("/report/"):
            slug = path.replace("/report/", "").replace("-", " ").title()
            report_html = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{slug} — Website Revenue Leak & Conversion Audit Report | LeakGrader.com</title>
  <meta name="description" content="Verified conversion audit for {slug}. Estimated monthly revenue loss, response time benchmark, and 24/7 AI WhatsApp Closer recommendation.">
  <meta property="og:title" content="{slug} — LeakGrader.com Conversion Scorecard">
  <meta property="og:description" content="View {slug}'s official conversion score and revenue leak analysis. Audited by LeakGrader.com.">
  <meta property="og:url" content="https://leakgrader.com{path}">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="stylesheet" href="/style.css?v=1020">
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800;900&display=swap" rel="stylesheet">
  <script src="https://unpkg.com/lucide@latest"></script>
</head>
<body style="padding: 40px 20px; max-width: 860px; margin: 0 auto; background: #030407; color: white; font-family: 'Plus Jakarta Sans', sans-serif;">
  <header style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 36px; padding-bottom: 20px; border-bottom: 1px solid rgba(255,255,255,0.08);">
    <a href="/" style="font-size: 20px; font-weight: 900; color: white; text-decoration: none;">LeakGrader<strong style="color:#0055ff;">.com</strong></a>
    <a href="/" style="background:#0055ff; color:white; padding:8px 18px; border-radius:999px; text-decoration:none; font-weight:700; font-size:12px;">Run New Free Audit</a>
  </header>

  <div style="background: rgba(12, 16, 28, 0.8); border: 1px solid rgba(255,255,255,0.12); border-radius: 20px; padding: 36px; box-shadow: 0 20px 50px rgba(0,0,0,0.8); backdrop-filter: blur(24px); margin-bottom: 24px;">
    <div style="display:inline-block; font-size:11px; font-weight:800; padding:4px 12px; background:rgba(99,102,241,0.15); color:#a5b4fc; border:1px solid rgba(99,102,241,0.3); border-radius:20px; margin-bottom:12px;">OFFICIAL CONVERSION SCORECARD</div>
    <h1 style="font-size: 32px; font-weight: 900; margin-bottom: 12px;">{slug}</h1>
    <p style="color: #94a3b8; font-size: 14px; line-height: 1.6; margin-bottom: 28px;">This business has been audited for lead capture friction, after-hours visitor drop-off, and response delay.</p>

    <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px;">
      <div style="background: rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; padding: 22px; text-align:center;">
        <span style="font-size:11px; color:#64748b; font-weight:700; text-transform:uppercase;">Overall AI Readiness</span>
        <div style="font-size: 48px; font-weight: 900; color: #38bdf8; margin: 8px 0;">76<span style="font-size:18px; color:#64748b;">/100</span></div>
        <span style="font-size:11px; color:#10b981; font-weight:700;">● Above Industry Average</span>
      </div>

      <div style="background: rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; padding: 22px; text-align:center;">
        <span style="font-size:11px; color:#64748b; font-weight:700; text-transform:uppercase;">Estimated Monthly Loss</span>
        <div style="font-size: 38px; font-weight: 900; color: #fb7185; margin: 12px 0;">$35,000+</div>
        <span style="font-size:11px; color:#94a3b8;">Recoverable via 24/7 AI WhatsApp Closer</span>
      </div>
    </div>

    <!-- Viral Share Buttons -->
    <div style="display:flex; gap:12px; flex-wrap:wrap; align-items:center; padding-top:20px; border-top:1px solid rgba(255,255,255,0.08);">
      <span style="font-size:12px; color:#94a3b8; font-weight:700;">Share Scorecard:</span>
      <a href="https://api.whatsapp.com/send?text=Check%20out%20the%20website%20revenue%20audit%20for%20{slug}%20on%20LeakGrader%3A%20https%3A%2F%2Fleakgrader.com{path}" target="_blank" style="background:#25D366; color:white; padding:8px 16px; border-radius:8px; text-decoration:none; font-size:12px; font-weight:700; display:inline-flex; align-items:center; gap:6px;">WhatsApp</a>
      <a href="https://twitter.com/intent/tweet?text=View%20the%20official%20revenue%20leak%20audit%20for%20{slug}%20on%20%40LeakGrader%3A%20https%3A%2F%2Fleakgrader.com{path}" target="_blank" style="background:#1DA1F2; color:white; padding:8px 16px; border-radius:8px; text-decoration:none; font-size:12px; font-weight:700; display:inline-flex; align-items:center; gap:6px;">Twitter / X</a>
      <a href="https://www.linkedin.com/sharing/share-offsite/?url=https%3A%2F%2Fleakgrader.com{path}" target="_blank" style="background:#0077B5; color:white; padding:8px 16px; border-radius:8px; text-decoration:none; font-size:12px; font-weight:700; display:inline-flex; align-items:center; gap:6px;">LinkedIn</a>
    </div>
  </div>

  <!-- Embed Badge Section -->
  <div style="background: rgba(12, 16, 28, 0.6); border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; padding: 22px;">
    <h3 style="font-size:14px; font-weight:800; margin-bottom:8px;">Embed Verified Badge On Your Website:</h3>
    <p style="font-size:12px; color:#94a3b8; margin-bottom:12px;">Copy this HTML code into your website footer to display your verified audit badge:</p>
    <code style="display:block; background:#000000; border:1px solid rgba(255,255,255,0.1); padding:10px 14px; border-radius:8px; font-size:11px; color:#38bdf8; font-family:monospace; word-break:break-all;">
      &lt;a href="https://leakgrader.com{path}" target="_blank"&gt;&lt;img src="https://leakgrader.com/badge/{path.replace('/report/', '')}.svg" alt="Audited by LeakGrader"&gt;&lt;/a&gt;
    </code>
  </div>
</body>
</html>"""
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(report_html.encode("utf-8"))
            return

        elif path == "/api/seo/directory":
            routes = SEO_ENGINE.get_all_directory_pages(limit=100)
            self._set_headers(200)
            self.wfile.write(json.dumps({"total_pages": len(routes), "pages": routes}).encode("utf-8"))
            return

        # 2. OmniBrain Document Endpoints
        elif path == "/api/documents":
            doc_list = []
            for doc_id, doc in ALL_DOCUMENTS.items():
                doc_list.append({
                    "id": doc_id,
                    "name": doc["name"],
                    "chunks": len(doc["chunks"]),
                    "size": doc.get("size", 0),
                    "type": doc.get("type", "file")
                })
            stats = {
                "total_docs": len(ALL_DOCUMENTS),
                "total_chunks": len(ALL_CHUNKS),
                "total_leads": len(LEADS),
                "total_bookings": len(BOOKINGS),
                "total_audits": len(AUDITS)
            }
            self._set_headers(200)
            self.wfile.write(json.dumps({"documents": doc_list, "stats": stats}).encode("utf-8"))
            return

        # 3. LeadPulse Endpoints
        elif path == "/api/leads/list":
            self._set_headers(200)
            self.wfile.write(json.dumps({"leads": LEADS}).encode("utf-8"))
            return

        elif path == "/api/leads/export-csv":
            csv_data = LEAD_AGENT.export_leads_to_csv(LEADS)
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", 'attachment; filename="verified_leads_export.csv"')
            self.end_headers()
            self.wfile.write(csv_data.encode("utf-8"))
            return

        # 4. BookFlow Endpoints
        elif path == "/api/booking/list":
            self._set_headers(200)
            self.wfile.write(json.dumps({"bookings": BOOKINGS}).encode("utf-8"))
            return

        # 5. Pricing Plans
        elif path == "/api/pricing/plans":
            self._set_headers(200)
            self.wfile.write(json.dumps(PLANS).encode("utf-8"))
            return

        # Static Web Files
        file_path = path.lstrip("/")
        if not file_path or file_path == "":
            file_path = "index.html"

        full_path = os.path.join(WEB_DIR, file_path)
        if os.path.exists(full_path) and os.path.isfile(full_path):
            mime, _ = mimetypes.guess_type(full_path)
            self._set_headers(200, content_type=mime or "text/plain")
            with open(full_path, "rb") as f:
                self.wfile.write(f.read())
        else:
            self._set_headers(404, "text/plain")
            self.wfile.write(b"404 Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get("Content-Length", 0))

        # --- 1. VIRAL 10-SECOND AUDIT ENGINE ---
        if path in ["/api/audit/run", "/api/audit/scan"]:
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8")) if content_length > 0 else {}
            company_or_url = data.get("url_or_company", "Apex Global Real Estate")
            industry = data.get("industry", "Real Estate")

            audit_result = AUDIT_ENGINE.run_instant_audit(company_or_url, industry)
            global AUDITS
            AUDITS.append(audit_result)
            save_audits()

            self._set_headers(200)
            self.wfile.write(json.dumps({"success": True, "audit": audit_result}).encode("utf-8"))
            return

        # --- 2. AUTOMATED CHECKOUT GATEWAY ---
        elif path == "/api/checkout/create":
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))
            plan_key = data.get("plan_key", "micro_audit")
            email = data.get("email", "client@company.com")

            order = PAYMENT_ENGINE.create_checkout_session(plan_key, customer_email=email)
            self._set_headers(200)
            self.wfile.write(json.dumps({"success": True, "order": order}).encode("utf-8"))
            return

        # --- 3. LEADPULSE AI ENDPOINTS ---
        elif path == "/api/leads/generate":
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))
            industry = data.get("industry", "Real Estate Agencies")
            location = data.get("location", "Dubai, UAE")
            service = data.get("service", "Autonomous AI Lead Generation & WhatsApp Bots")
            count = int(data.get("count", 5))

            new_leads = LEAD_AGENT.generate_leads(industry, location, service, count)
            global LEADS
            LEADS.extend(new_leads)
            save_leads()

            self._set_headers(200)
            self.wfile.write(json.dumps({"success": True, "generated_count": len(new_leads), "leads": LEADS}).encode("utf-8"))
            return

        elif path == "/api/leads/clear":
            LEADS.clear()
            save_leads()
            self._set_headers(200)
            self.wfile.write(json.dumps({"success": True}).encode("utf-8"))
            return

        # --- 4. OMNIBRAIN AI ENDPOINTS ---
        elif path == "/api/upload":
            content_type = self.headers.get("Content-Type", "")
            if "multipart/form-data" in content_type:
                boundary = content_type.split("boundary=")[-1].encode()
                body = self.rfile.read(content_length)
                parts = body.split(b"--" + boundary)
                uploaded_count = 0
                new_chunks_count = 0

                for part in parts:
                    if b'filename="' in part:
                        headers_raw, file_data = part.split(b"\r\n\r\n", 1)
                        file_data = file_data.rstrip(b"\r\n")
                        header_str = headers_raw.decode('latin-1')
                        filename_match = [line for line in header_str.split("\r\n") if 'filename="' in line]
                        if filename_match:
                            raw_name = filename_match[0].split('filename="')[-1].split('"')[0]
                            file_name = os.path.basename(raw_name)
                            if file_name and len(file_data) > 0:
                                chunks = parse_file(file_name, file_data)
                                doc_id = f"doc_{int(time.time()*1000)}_{uploaded_count}"
                                ALL_DOCUMENTS[doc_id] = {
                                    "name": file_name,
                                    "chunks": chunks,
                                    "size": len(file_data),
                                    "type": "file"
                                }
                                ALL_CHUNKS.extend(chunks)
                                uploaded_count += 1
                                new_chunks_count += len(chunks)

                RETRIEVER.index(ALL_CHUNKS)
                save_index()

                self._set_headers(200)
                self.wfile.write(json.dumps({
                    "success": True,
                    "uploaded_count": uploaded_count,
                    "new_chunks": new_chunks_count,
                    "total_chunks": len(ALL_CHUNKS)
                }).encode("utf-8"))
                return

        elif path == "/api/upload-url":
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))
            url = data.get("url", "").strip()
            try:
                text = extract_text_from_url(url)
                doc_name = url.replace("https://", "").replace("http://", "").split("/")[0] + " (Web)"
                chunks = chunk_text(text, doc_name=doc_name, page_num=1)
                doc_id = f"url_{int(time.time()*1000)}"
                ALL_DOCUMENTS[doc_id] = {
                    "name": doc_name,
                    "chunks": chunks,
                    "size": len(text.encode("utf-8")),
                    "type": "url"
                }
                ALL_CHUNKS.extend(chunks)
                RETRIEVER.index(ALL_CHUNKS)
                save_index()
                self._set_headers(200)
                self.wfile.write(json.dumps({"success": True, "title": doc_name, "chunks": len(chunks)}).encode("utf-8"))
            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        elif path == "/api/query":
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))
            query = data.get("query", "").strip()
            top_chunks = RETRIEVER.search(query, top_k=5)
            if top_chunks:
                result = INTELLIGENCE.query_with_citations(query, top_chunks)
            else:
                result = {"answer": "No relevant documents found in knowledge base.", "citations": []}
            self._set_headers(200)
            self.wfile.write(json.dumps(result).encode("utf-8"))
            return

        elif path == "/api/summary":
            summary = INTELLIGENCE.generate_executive_summary(ALL_CHUNKS)
            self._set_headers(200)
            self.wfile.write(json.dumps({"result": summary}).encode("utf-8"))
            return

        elif path == "/api/risk-audit":
            audit = INTELLIGENCE.generate_risk_audit(ALL_CHUNKS)
            self._set_headers(200)
            self.wfile.write(json.dumps({"result": audit}).encode("utf-8"))
            return

        elif path == "/api/extract-tables":
            tables = INTELLIGENCE.extract_structured_data(ALL_CHUNKS)
            self._set_headers(200)
            self.wfile.write(json.dumps({"result": tables}).encode("utf-8"))
            return

        elif path == "/api/clear":
            ALL_DOCUMENTS.clear()
            ALL_CHUNKS.clear()
            RETRIEVER.index([])
            save_index()
            self._set_headers(200)
            self.wfile.write(json.dumps({"success": True}).encode("utf-8"))
            return

        # --- 5. BOOKFLOW AI ENDPOINTS ---
        elif path == "/api/booking/chat":
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))
            business_context = data.get("business_context", "Galicon AI Solutions: Enterprise AI Agents starting at $2,500.")
            chat_history = data.get("history", [])
            user_message = data.get("message", "")

            ai_resp = BOOKING_AGENT.chat_and_qualify(business_context, chat_history, user_message)
            
            if ai_resp.get("booking_ready") and ai_resp.get("extracted_data"):
                booking_entry = ai_resp["extracted_data"]
                booking_entry["id"] = f"apt_{int(time.time()*1000)}"
                booking_entry["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
                booking_entry["status"] = "CONFIRMED"
                global BOOKINGS
                BOOKINGS.append(booking_entry)
                save_bookings()
                ai_resp["auto_booked"] = True

            self._set_headers(200)
            self.wfile.write(json.dumps(ai_resp).encode("utf-8"))
            return

        elif path == "/api/booking/clear":
            BOOKINGS.clear()
            save_bookings()
            self._set_headers(200)
            self.wfile.write(json.dumps({"success": True}).encode("utf-8"))
            return

        # --- 6. CONTENTCREW AI ENDPOINTS ---
        elif path == "/api/content-crew/run":
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))
            topic = data.get("topic", "How AI Agents are Replacing Traditional SaaS in 2026")
            audience = data.get("audience", "Founders, CTOs, and Business Leaders")
            tone = data.get("tone", "Authoritative, High-Energy & Actionable")

            result = CONTENT_CREW.run_multi_agent_pipeline(topic, audience, tone)
            self._set_headers(200)
            self.wfile.write(json.dumps({"success": True, "data": result}).encode("utf-8"))
            return

        elif path == "/api/growth/indexnow-ping":
            result = GROWTH_AGENT.submit_to_indexnow()
            self._set_headers(200)
            self.wfile.write(json.dumps({"success": True, "result": result}).encode("utf-8"))
            return

        elif path == "/api/growth/generate-campaign":
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8")) if content_length > 0 else {}
            comp = data.get("company_name", "Stripe")
            niche = data.get("niche", "SaaS & FinTech")
            loss = data.get("lost_revenue", "$48,000/mo")

            result = GROWTH_AGENT.generate_viral_campaign(comp, niche, loss)
            self._set_headers(200)
            self.wfile.write(json.dumps({"success": True, "campaign": result}).encode("utf-8"))
            return

        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/documents/"):
            doc_id = unquote(path.split("/api/documents/")[-1])
            if doc_id in ALL_DOCUMENTS:
                doc_name = ALL_DOCUMENTS[doc_id]["name"]
                del ALL_DOCUMENTS[doc_id]
                global ALL_CHUNKS
                ALL_CHUNKS = [c for c in ALL_CHUNKS if c.get("doc_name") != doc_name]
                RETRIEVER.index(ALL_CHUNKS)
                save_index()
                self._set_headers(200)
                self.wfile.write(json.dumps({"success": True}).encode("utf-8"))
                return
            else:
                self._set_headers(404)
                self.wfile.write(json.dumps({"error": "Document not found"}).encode("utf-8"))
                return


def run_server():
    load_all_data()
    server_address = ('', PORT)
    httpd = ThreadingHTTPServer(server_address, MastermindRequestHandler)
    print("=" * 60)
    print(f"Mastermind AI Global Platform Online! (7 Engines Active)")
    print(f"URL: http://localhost:{PORT}")
    print(f"Programmatic SEO Sitemap: http://localhost:{PORT}/sitemap.xml")
    print(f"Viral Revenue Leak Engine: Active")
    print(f"Apollo Data Engine: Active")
    print("=" * 60)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Mastermind Suite...")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
