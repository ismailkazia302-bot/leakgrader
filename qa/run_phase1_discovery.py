import os
import sys
import json
import re
import subprocess

qa_dir = os.path.dirname(os.path.abspath(__file__))
omnibrain_dir = os.path.abspath(os.path.join(qa_dir, ".."))
evidence_dir = os.path.join(qa_dir, "evidence")
os.makedirs(evidence_dir, exist_ok=True)

discovery_results = {}

# 1. Frontend Framework & Version
web_dir = os.path.join(omnibrain_dir, "web")
index_html = os.path.join(web_dir, "index.html")

frontend_info = {
    "framework": "Vanilla HTML5 / Modern CSS3 / Vanilla ECMAScript (ES6+)",
    "version": "Custom Modular Architecture (Zero external JS frameworks)",
    "libraries_cdn": [],
    "pwa_support": False
}

if os.path.exists(index_html):
    with open(index_html, "r", encoding="utf-8", errors="ignore") as f:
        html_content = f.read()
        if "manifest.json" in html_content:
            frontend_info["pwa_support"] = True
        cdns = re.findall(r'<script[^>]+src=["\'](https?://[^"\']+)["\']', html_content)
        cdns_css = re.findall(r'<link[^>]+href=["\'](https?://[^"\']+)["\']', html_content)
        frontend_info["libraries_cdn"] = list(set(cdns + cdns_css))

discovery_results["frontend"] = frontend_info

# 2. Backend Framework
req_txt = os.path.join(omnibrain_dir, "requirements.txt")
backend_info = {
    "runtime": "Python 3.10+ (Standard Library http.server / ThreadingHTTPServer)",
    "production_server": "Gunicorn 21.2.0+ (WSGI via wsgi.py)",
    "dependencies": []
}
if os.path.exists(req_txt):
    with open(req_txt, "r", encoding="utf-8") as f:
        backend_info["dependencies"] = [line.strip() for line in f if line.strip() and not line.startswith("#")]

discovery_results["backend"] = backend_info

# 3. Database & Authentication Provider
storage_dir = os.path.join(omnibrain_dir, "storage")
db_files = os.listdir(storage_dir) if os.path.exists(storage_dir) else []
discovery_results["database"] = {
    "type": "File-based JSON Document Store (Flat-file NoSQL)",
    "storage_directory": "storage/",
    "active_tables_json": db_files,
    "rdbms_or_cloud_db": "None (Flat-file JSON, no external PostgreSQL/MySQL/Firestore)"
}

discovery_results["authentication"] = {
    "provider": "None / Anonymous Session-based with Token check on Founder route",
    "user_table": "No user/credentials database table exists",
    "public_endpoints_auth": "Unauthenticated (Open REST endpoints)",
    "admin_dashboard": "/founder route is protected by founder_token query param / password, or open default"
}

# 4. Hosting & Deployment Provider
dockerfile = os.path.exists(os.path.join(omnibrain_dir, "Dockerfile"))
render_yaml = os.path.exists(os.path.join(omnibrain_dir, "render.yaml"))
procfile = os.path.exists(os.path.join(omnibrain_dir, "Procfile"))
discovery_results["hosting"] = {
    "primary_cloud": "Render (render.yaml, Procfile, gunicorn wsgi:app)",
    "fallback_tunnel": "Cloudflare Tunnel (cloudflared.exe present in repo)",
    "containerization": f"Dockerfile present: {dockerfile}"
}

# 5. Payment Provider
payment_cfg = os.path.join(omnibrain_dir, "config", "payment_links.json")
payment_info = {
    "provider": "Lemon Squeezy",
    "mode": "PRODUCTION / LIVE",
    "links_configured": False
}
if os.path.exists(payment_cfg):
    try:
        with open(payment_cfg, "r", encoding="utf-8") as f:
            p_data = json.load(f)
            payment_info["links_configured"] = True
            payment_info["plans"] = list(p_data.keys())
            first_url = list(p_data.values())[0].get("checkout_url", "")
            if "sandbox" in first_url.lower():
                payment_info["mode"] = "SANDBOX"
            else:
                payment_info["mode"] = "LIVE / PRODUCTION (Transactions must be BLOCKED per safety rule 9)"
    except Exception as e:
        payment_info["error"] = str(e)

discovery_results["payment"] = payment_info

# 6. AI Model Providers
discovery_results["ai_models"] = {
    "primary_cloud_model": "Google Gemini (Gemini 1.5 Flash / Pro via GEMINI_API_KEY)",
    "local_fallbacks": "Deterministic Heuristic Generators, Regex Parser, Dynamic Template Synthesis",
    "llm_orchestration": "Direct Google Generative Language REST endpoints via urllib"
}

# 7. Main API Routes (parsed from app.py)
app_py = os.path.join(omnibrain_dir, "app.py")
api_routes = []
if os.path.exists(app_py):
    with open(app_py, "r", encoding="utf-8") as f:
        app_code = f.read()
        get_paths = re.findall(r'self\.path\s*(?:==|\.startswith\()\s*["\']([^"\']+)["\']', app_code)
        api_routes = sorted(list(set(get_paths)))

discovery_results["api_routes"] = api_routes

# 8. Environment separation & Sandbox
discovery_results["environments"] = {
    "separate_staging_or_dev": False,
    "environment_detection": "Environment variables only (PORT, GEMINI_API_KEY, SMTP_*, RENDER=true)",
    "test_sandbox_mode": False
}

# 9. Real vs Mocked/Fallback/Demo Data
discovery_results["feature_data_sources"] = {
    "revenue_leak_scanner": "Hybrid: Performs live HTTP/DNS/SSL probes, calculates real latency/drop-offs; uses mathematical formula model for financial leak projections.",
    "b2b_prospect_search": "Dual-mode: Has local pre-compiled and synthetic business pools in lead_gen_agent.py; recently augmented with real curated GMB data.",
    "ai_closer_crm": "Real Gemini LLM when API key present; falls back to deterministic rule-based dialogue tree when offline.",
    "document_vault_rag": "Real in-memory TF-IDF and hybrid keyword retriever; parses actual uploaded PDF/TXT/CSV/JSON files.",
    "seo_article_factory": "Real Gemini LLM generation with fallback multi-stage article template assembler.",
    "email_outreach": "Real Gmail SMTP dispatcher (port 587 TLS) configured with live verified Google App Password."
}

# 10. Server-Side Entitlement Checks
discovery_results["entitlements"] = {
    "server_side_enforcement": False,
    "details": "Core endpoints (/api/audit, /api/prospects, /api/chat, /api/seo/generate, /api/upload) do NOT enforce a signed JWT, session token, or active license key check. Anyone can call endpoints directly without paying."
}

# 11. Git Status
try:
    git_proc = subprocess.run(["git", "status", "--porcelain"], cwd=omnibrain_dir, capture_output=True, text=True)
    git_uncommitted = [l.strip() for l in git_proc.stdout.strip().split("\n") if l.strip()]
    discovery_results["git_status"] = {
        "clean": len(git_uncommitted) == 0,
        "uncommitted_files": git_uncommitted
    }
except Exception as e:
    discovery_results["git_status"] = {"error": str(e)}

out_file = os.path.join(evidence_dir, "phase1_discovery.json")
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(discovery_results, f, indent=2)

print(f"[PHASE 1 DISCOVERY COMPLETE] Output saved to {out_file}")
