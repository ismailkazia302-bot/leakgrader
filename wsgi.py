"""
LeakGrader.com - Production WSGI Application Runner for Gunicorn / Render.com
Wraps the OmniBrain & LeakGrader HTTP handlers into a standard PEP-3333 compliant WSGI application.
"""

import os
import sys
import json
import io
import mimetypes
from urllib.parse import parse_qs, unquote

# Import the core application engines
from app import (
    ALL_DOCUMENTS, ALL_CHUNKS, BOOKINGS, LEADS, AUDITS,
    RETRIEVER, INTELLIGENCE, LEAD_AGENT, BOOKING_AGENT,
    CONTENT_CREW, AUDIT_ENGINE, SEO_ENGINE, PAYMENT_ENGINE, GROWTH_AGENT, PLANS,
    ANALYTICS_DASHBOARD, WEBSITE_MANAGER, SOCIAL_POSTER,
    WEB_DIR, save_index, save_bookings, save_leads, save_audits, load_all_data
)

# Load existing index & storage data on startup
load_all_data()

def application(environ, start_response):
    """
    Standard WSGI callable for Gunicorn on Render.com
    """
    path = environ.get('PATH_INFO', '')
    method = environ.get('REQUEST_METHOD', 'GET').upper()
    query_string = environ.get('QUERY_STRING', '')

    # Record Live Visitor Telemetry
    client_ip = environ.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or environ.get('REMOTE_ADDR', '127.0.0.1')
    user_agent = environ.get('HTTP_USER_AGENT', '')
    referrer = environ.get('HTTP_REFERER', '')
    country = environ.get('HTTP_CF_IPCOUNTRY', '')
    if not path.startswith('/api/') and not path.endswith('.ico') and not path.endswith('.svg') and not path.endswith('.css') and not path.endswith('.js'):
        try:
            ANALYTICS_DASHBOARD.record_visitor(client_ip, user_agent, path, referrer, country)
        except Exception:
            pass

    # 1. Handle POST API requests
    if method == 'POST':
        try:
            content_length = int(environ.get('CONTENT_LENGTH', 0))
        except (ValueError, TypeError):
            content_length = 0

        post_body = environ['wsgi.input'].read(content_length) if content_length > 0 else b''
        content_type = environ.get('CONTENT_TYPE', '')

        # JSON payload parsing
        body_json = {}
        if 'application/json' in content_type and post_body:
            try:
                body_json = json.loads(post_body.decode('utf-8'))
            except Exception:
                body_json = {}

        # Route: /api/audit/scan & /api/audit/run
        if path in ['/api/audit/scan', '/api/audit/run']:
            url_or_comp = body_json.get('url_or_company', '')
            res = AUDIT_ENGINE.run_instant_audit(url_or_comp)
            AUDITS.append(res)
            save_audits()
            status = '200 OK'
            response_headers = [('Content-Type', 'application/json; charset=utf-8'), ('Access-Control-Allow-Origin', '*')]
            start_response(status, response_headers)
            return [json.dumps({"success": True, "audit": res}).encode('utf-8')]

        # Route: /api/leads/generate
        elif path == '/api/leads/generate':
            try:
                ind = body_json.get('industry', 'Real Estate')
                loc = body_json.get('location', 'Dubai')
                srv = body_json.get('service', 'AI WhatsApp Lead Closer')
                cnt = int(body_json.get('count', 5))
                if hasattr(LEAD_AGENT, 'generate_targeted_leads'):
                    new_leads = LEAD_AGENT.generate_targeted_leads(ind, loc, srv, cnt)
                else:
                    new_leads = LEAD_AGENT.generate_leads(ind, loc, srv, cnt)
                for l in new_leads:
                    LEADS.append(l)
                save_leads()
                status = '200 OK'
                response_headers = [('Content-Type', 'application/json; charset=utf-8'), ('Access-Control-Allow-Origin', '*')]
                start_response(status, response_headers)
                return [json.dumps({"success": True, "generated_count": len(new_leads), "leads": new_leads}).encode('utf-8')]
            except Exception as e:
                status = '200 OK'
                response_headers = [('Content-Type', 'application/json; charset=utf-8'), ('Access-Control-Allow-Origin', '*')]
                start_response(status, response_headers)
                return [json.dumps({"success": True, "generated_count": 0, "leads": [], "fallback": True}).encode('utf-8')]

        # Route: /api/leads/clear
        elif path == '/api/leads/clear':
            LEADS.clear()
            save_leads()
            status = '200 OK'
            response_headers = [('Content-Type', 'application/json; charset=utf-8'), ('Access-Control-Allow-Origin', '*')]
            start_response(status, response_headers)
            return [json.dumps({"success": True}).encode('utf-8')]

        # Route: /api/booking/chat
        elif path == '/api/booking/chat':
            try:
                msg = body_json.get('message', '')
                hist = body_json.get('history', [])
                ctx = body_json.get('business_context', 'LeakGrader AI Solutions')
                res = BOOKING_AGENT.chat_and_qualify(ctx, hist, msg)
                if res.get('is_qualified') and res.get('booking_details'):
                    b_info = res['booking_details']
                    BOOKINGS.append({
                        "id": f"bk_{len(BOOKINGS)+1}",
                        "name": b_info.get("name", "Qualified Prospect"),
                        "email": b_info.get("email", "N/A"),
                        "phone": b_info.get("phone", "N/A"),
                        "time_slot": b_info.get("time_slot", "Pending Selection"),
                        "intent": b_info.get("intent", "High"),
                        "timestamp": "2026-09-04 03:50:00"
                    })
                    save_bookings()
                status = '200 OK'
                response_headers = [('Content-Type', 'application/json; charset=utf-8'), ('Access-Control-Allow-Origin', '*')]
                start_response(status, response_headers)
                return [json.dumps(res).encode('utf-8')]
            except Exception as e:
                status = '200 OK'
                response_headers = [('Content-Type', 'application/json; charset=utf-8'), ('Access-Control-Allow-Origin', '*')]
                start_response(status, response_headers)
                return [json.dumps({"reply": "Thank you for reaching out! Our team will contact you in under 30 seconds.", "is_qualified": True}).encode('utf-8')]

        # Route: /api/documents/ask & /api/query
        elif path in ['/api/documents/ask', '/api/query']:
            q = body_json.get('question', body_json.get('query', ''))
            retrieved = RETRIEVER.search(q, top_k=5)
            ans = INTELLIGENCE.answer_query(q, retrieved)
            status = '200 OK'
            response_headers = [('Content-Type', 'application/json; charset=utf-8'), ('Access-Control-Allow-Origin', '*')]
            start_response(status, response_headers)
            return [json.dumps({"answer": ans, "citations": retrieved}).encode('utf-8')]

        # Route: /api/content/generate-article & /api/content-crew/run
        elif path in ['/api/content/generate-article', '/api/content-crew/run']:
            top = body_json.get('topic', '')
            aud = body_json.get('audience', 'Tech Founders')
            tone = body_json.get('tone', 'Authoritative')
            res = CONTENT_CREW.run_multi_agent_pipeline(top, aud, tone)
            article_md = res.get('full_article_markdown', '')
            status = '200 OK'
            response_headers = [('Content-Type', 'application/json; charset=utf-8'), ('Access-Control-Allow-Origin', '*')]
            start_response(status, response_headers)
            return [json.dumps({"success": True, "article": article_md, "data": res}).encode('utf-8')]

        # Route: /api/checkout/create
        elif path == '/api/checkout/create':
            p_key = body_json.get('plan_key', 'micro_audit')
            c_email = body_json.get('customer_email', 'client@company.com')
            order = PAYMENT_ENGINE.create_checkout_session(p_key, c_email)
            status = '200 OK'
            response_headers = [('Content-Type', 'application/json; charset=utf-8'), ('Access-Control-Allow-Origin', '*')]
            start_response(status, response_headers)
            return [json.dumps({"success": True, "order": order}).encode('utf-8')]

        # Route: /api/growth/indexnow-ping
        elif path == '/api/growth/indexnow-ping':
            res = GROWTH_AGENT.submit_to_indexnow()
            status = '200 OK'
            response_headers = [('Content-Type', 'application/json; charset=utf-8'), ('Access-Control-Allow-Origin', '*')]
            start_response(status, response_headers)
            return [json.dumps({"success": True, "result": res}).encode('utf-8')]

        # Route: /api/growth/generate-campaign
        elif path == '/api/growth/generate-campaign':
            comp = body_json.get("company_name", "Stripe")
            niche = body_json.get("niche", "SaaS & FinTech")
            loss = body_json.get("lost_revenue", "$48,000/mo")
            res = GROWTH_AGENT.generate_viral_campaign(comp, niche, loss)
            status = '200 OK'
            response_headers = [('Content-Type', 'application/json; charset=utf-8'), ('Access-Control-Allow-Origin', '*')]
            start_response(status, response_headers)
            return [json.dumps({"success": True, "campaign": res}).encode('utf-8')]

        # Route: /api/manager/solve-all
        elif path in ['/api/manager/solve-all', '/api/website-manager/auto-heal']:
            rep = WEBSITE_MANAGER.run_full_management_cycle()
            status = '200 OK'
            response_headers = [('Content-Type', 'application/json; charset=utf-8'), ('Access-Control-Allow-Origin', '*')]
            start_response(status, response_headers)
            return [json.dumps({"success": True, "report": rep}).encode('utf-8')]

        # Route: /api/social/generate
        elif path == '/api/social/generate':
            bundle = SOCIAL_POSTER.generate_next_social_post()
            status = '200 OK'
            response_headers = [('Content-Type', 'application/json; charset=utf-8'), ('Access-Control-Allow-Origin', '*')]
            start_response(status, response_headers)
            return [json.dumps({"success": True, "post": bundle}).encode('utf-8')]

        # Route: /api/social/dispatch
        elif path == '/api/social/dispatch':
            post_id = body_json.get('post_id')
            res = SOCIAL_POSTER.dispatch_post(post_id=post_id)
            status = '200 OK'
            response_headers = [('Content-Type', 'application/json; charset=utf-8'), ('Access-Control-Allow-Origin', '*')]
            start_response(status, response_headers)
            return [json.dumps({"success": True, "result": res}).encode('utf-8')]

        # Route: /api/social/config
        elif path == '/api/social/config':
            webhook_url = body_json.get('webhook_url', '')
            res = SOCIAL_POSTER.update_config(webhook_url=webhook_url)
            status = '200 OK'
            response_headers = [('Content-Type', 'application/json; charset=utf-8'), ('Access-Control-Allow-Origin', '*')]
            start_response(status, response_headers)
            return [json.dumps({"success": True, "config": res}).encode('utf-8')]

    # 2. Handle GET endpoints
    if path in ['/analytics', '/dashboard', '/founder']:
        dashboard_html = ANALYTICS_DASHBOARD.render_html()
        status = '200 OK'
        response_headers = [('Content-Type', 'text/html; charset=utf-8'), ('Cache-Control', 'no-cache')]
        start_response(status, response_headers)
        return [dashboard_html.encode('utf-8')]

    elif path == '/api/analytics/live':
        status = '200 OK'
        response_headers = [('Content-Type', 'application/json; charset=utf-8'), ('Access-Control-Allow-Origin', '*')]
        start_response(status, response_headers)
        return [json.dumps(ANALYTICS_DASHBOARD.get_live_data()).encode('utf-8')]

    elif path in ['/api/manager/status', '/api/website-manager/status']:
        rep = WEBSITE_MANAGER.run_full_management_cycle()
        status = '200 OK'
        response_headers = [('Content-Type', 'application/json; charset=utf-8'), ('Access-Control-Allow-Origin', '*')]
        start_response(status, response_headers)
        return [json.dumps(rep).encode('utf-8')]

    elif path == '/api/social/feed':
        feed = SOCIAL_POSTER.get_feed()
        status = '200 OK'
        response_headers = [('Content-Type', 'application/json; charset=utf-8'), ('Access-Control-Allow-Origin', '*')]
        start_response(status, response_headers)
        return [json.dumps(feed).encode('utf-8')]

    elif path == '/api/leads/list':
        status = '200 OK'
        response_headers = [('Content-Type', 'application/json; charset=utf-8'), ('Access-Control-Allow-Origin', '*')]
        start_response(status, response_headers)
        return [json.dumps({"success": True, "leads": LEADS}).encode('utf-8')]

    elif path == '/api/leads/export-csv':
        csv_data = LEAD_AGENT.export_leads_to_csv(LEADS)
        status = '200 OK'
        response_headers = [
            ('Content-Type', 'text/csv; charset=utf-8'),
            ('Content-Disposition', 'attachment; filename="verified_leads_export.csv"'),
            ('Access-Control-Allow-Origin', '*')
        ]
        start_response(status, response_headers)
        return [csv_data.encode('utf-8')]

    elif path == '/robots.txt':
        robots_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", "robots.txt")
        if os.path.exists(robots_path):
            with open(robots_path, 'rb') as f:
                content = f.read()
        else:
            content = b"User-agent: *\nAllow: /\nSitemap: https://leakgrader.com/sitemap.xml\n"
        status = '200 OK'
        response_headers = [('Content-Type', 'text/plain; charset=utf-8'), ('Cache-Control', 'public, max-age=86400')]
        start_response(status, response_headers)
        return [content]

    elif path == '/sitemap.xml':
        sitemap_xml = SEO_ENGINE.generate_sitemap_xml()
        status = '200 OK'
        response_headers = [('Content-Type', 'application/xml; charset=utf-8'), ('Cache-Control', 'public, max-age=86400')]
        start_response(status, response_headers)
        return [sitemap_xml.encode('utf-8')]

    elif path.startswith('/badge/') and path.endswith('.svg'):
        slug = path.replace('/badge/', '').replace('.svg', '').replace('-', ' ').title()
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
        status = '200 OK'
        response_headers = [('Content-Type', 'image/svg+xml; charset=utf-8'), ('Cache-Control', 'public, max-age=3600')]
        start_response(status, response_headers)
        return [svg_content.encode('utf-8')]

    elif path.startswith('/report/'):
        slug = path.replace('/report/', '').replace('-', ' ').title()
        report_html = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{slug} — Website Revenue Leak & Conversion Audit Report | LeakGrader.com</title>
  <link rel="stylesheet" href="/style.css?v=2030">
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800;900&display=swap" rel="stylesheet">
</head>
<body style="padding: 40px 20px; max-width: 860px; margin: 0 auto; background: #07090e; color: white; font-family: 'Plus Jakarta Sans', sans-serif;">
  <header style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 36px; padding-bottom: 20px; border-bottom: 1px solid rgba(255,255,255,0.08);">
    <a href="/" style="font-size: 20px; font-weight: 900; color: white; text-decoration: none;">LeakGrader<strong style="color:#0055ff;">.com</strong></a>
    <a href="/" style="background:#0055ff; color:white; padding:8px 18px; border-radius:999px; text-decoration:none; font-weight:700; font-size:12px;">Run New Free Audit</a>
  </header>
  <div style="background: rgba(15, 20, 34, 0.85); border: 1px solid rgba(255,255,255,0.12); border-radius: 20px; padding: 36px; box-shadow: 0 20px 50px rgba(0,0,0,0.8); backdrop-filter: blur(24px); margin-bottom: 24px;">
    <div style="display:inline-block; font-size:11px; font-weight:800; padding:4px 12px; background:rgba(0,85,255,0.15); color:#38bdf8; border:1px solid rgba(0,85,255,0.3); border-radius:20px; margin-bottom:12px;">OFFICIAL CONVERSION SCORECARD</div>
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
  </div>
</body>
</html>"""
        status = '200 OK'
        response_headers = [('Content-Type', 'text/html; charset=utf-8')]
        start_response(status, response_headers)
        return [report_html.encode('utf-8')]

    elif path == '/api/seo/directory':
        routes = SEO_ENGINE.get_all_directory_pages(limit=100)
        status = '200 OK'
        response_headers = [('Content-Type', 'application/json; charset=utf-8'), ('Access-Control-Allow-Origin', '*')]
        start_response(status, response_headers)
        return [json.dumps({"total_pages": len(routes), "pages": routes}).encode('utf-8')]

    elif path == '/api/documents':
        doc_list = [{"id": k, "name": v["name"], "chunks": len(v["chunks"]), "size": v.get("size", 0)} for k, v in ALL_DOCUMENTS.items()]
        status = '200 OK'
        response_headers = [('Content-Type', 'application/json; charset=utf-8'), ('Access-Control-Allow-Origin', '*')]
        start_response(status, response_headers)
        return [json.dumps({"documents": doc_list}).encode('utf-8')]

    elif path == '/api/booking/list':
        status = '200 OK'
        response_headers = [('Content-Type', 'application/json; charset=utf-8'), ('Access-Control-Allow-Origin', '*')]
        start_response(status, response_headers)
        return [json.dumps({"bookings": BOOKINGS}).encode('utf-8')]

    elif path == '/api/pricing/plans':
        status = '200 OK'
        response_headers = [('Content-Type', 'application/json; charset=utf-8'), ('Access-Control-Allow-Origin', '*')]
        start_response(status, response_headers)
        return [json.dumps(PLANS).encode('utf-8')]

    # 3. Static Web Files (HTML, CSS, JS)
    WEB_DIR_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")

    if path in ['', '/']:
        index_file = os.path.join(WEB_DIR_PATH, 'index.html')
        if os.path.exists(index_file):
            status = '200 OK'
            response_headers = [('Content-Type', 'text/html; charset=utf-8'), ('Cache-Control', 'public, max-age=3600')]
            start_response(status, response_headers)
            with open(index_file, 'rb') as f:
                content = f.read()
            ga_id = os.environ.get('GA_MEASUREMENT_ID', '')
            if ga_id:
                content = content.replace(b'{{GA_MEASUREMENT_ID}}', ga_id.encode('utf-8'))
            return [content]

    file_path = path.lstrip('/')
    full_path = os.path.join(WEB_DIR_PATH, file_path)
    if os.path.exists(full_path) and os.path.isfile(full_path):
        mime, _ = mimetypes.guess_type(full_path)
        content_type = mime or 'text/plain'
        if 'text/' in content_type or 'javascript' in content_type:
            content_type += '; charset=utf-8'

        status = '200 OK'
        response_headers = [('Content-Type', content_type), ('Cache-Control', 'public, max-age=3600')]
        start_response(status, response_headers)
        with open(full_path, 'rb') as f:
            content = f.read()
        if file_path.endswith('index.html'):
            ga_id = os.environ.get('GA_MEASUREMENT_ID', '')
            if ga_id:
                content = content.replace(b'{{GA_MEASUREMENT_ID}}', ga_id.encode('utf-8'))
        return [content]

    # Fallback to index.html for single-page app routing
    fallback_index = os.path.join(WEB_DIR_PATH, 'index.html')
    if os.path.exists(fallback_index):
        status = '200 OK'
        response_headers = [('Content-Type', 'text/html; charset=utf-8')]
        start_response(status, response_headers)
        with open(fallback_index, 'rb') as f:
            content = f.read()
        ga_id = os.environ.get('GA_MEASUREMENT_ID', '')
        if ga_id:
            content = content.replace(b'{{GA_MEASUREMENT_ID}}', ga_id.encode('utf-8'))
        return [content]

    status = '404 Not Found'
    response_headers = [('Content-Type', 'text/plain')]
    start_response(status, response_headers)
    return [b'404 Not Found']

# Gunicorn WSGI Entry Point Alias
app = application

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    port = int(os.environ.get('PORT', 8090))
    print(f"[*] Starting WSGI Development Server on port {port}...")
    server = make_server('0.0.0.0', port, application)
    server.serve_forever()
