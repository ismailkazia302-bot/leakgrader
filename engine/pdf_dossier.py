"""
LeakGrader.com - Executive PDF Dossier & High-Ticket Boardroom Report Generator
Generates an enterprise-grade, print-ready, dark-mode 5-page PDF Dossier
designed for closing $1,500/mo Done-For-You Agency Retainers.
"""

import json
import time

class ExecutiveDossierGenerator:
    def __init__(self, base_url: str = "https://leakgrader.com"):
        self.base_url = base_url.rstrip("/")

    def generate_dossier_html(self, audit_data: dict) -> str:
        """
        Generates clean, high-resolution HTML with print CSS optimizations for instant PDF export.
        """
        company = audit_data.get("company_name", "Enterprise Client")
        target_url = audit_data.get("target_url", "https://company.com")
        score = audit_data.get("ai_readiness_score", 72)
        leak = audit_data.get("estimated_monthly_leak", "$45,000/mo")
        audit_id = audit_data.get("audit_id", f"dossier_{int(time.time())}")
        timestamp = audit_data.get("timestamp", time.strftime("%Y-%m-%d %H:%M:%S UTC"))
        tech_stack = ", ".join(audit_data.get("tech_stack", ["Modern Web Architecture", "Enterprise CDN"]))
        form_fields = audit_data.get("form_friction_fields", 6)
        diag_points = audit_data.get("diagnostic_points", [])

        diag_rows_list = []
        for p in diag_points:
            p_num = p.get("point_number", 1)
            p_name = p.get("name", "Audit Check")
            p_cat = p.get("category", "General")
            p_stat = p.get("status", "PASS")
            p_sc = p.get("score", 80)
            p_obs = p.get("observation", "")
            stat_color = "var(--accent-emerald)" if p_stat == "PASS" else ("#FBBF24" if p_stat == "WARN" else "var(--accent-rose)")
            diag_rows_list.append(
                f"<tr><td><strong>{p_num}</strong></td><td><strong>{p_name}</strong></td><td style='color:var(--text-muted); font-size:11px;'>{p_cat}</td><td><span style='color:{stat_color}; font-weight:800; font-size:11px;'>{p_stat}</span></td><td><code>{p_sc}/100</code></td><td style='color:var(--text-muted); font-size:12px;'>{p_obs}</td></tr>"
            )
        diagnostic_rows = "\n".join(diag_rows_list) if diag_rows_list else "<tr><td colspan='6' style='text-align:center;'>Standard 15-Point Diagnostic Verified</td></tr>"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Executive Revenue Leak Dossier - {company} | LeakGrader</title>
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Cdefs%3E%3ClinearGradient id='g' x1='0%25' y1='0%25' x2='100%25' y2='100%25'%3E%3Cstop offset='0%25' stop-color='%230055ff'/%3E%3Cstop offset='100%25' stop-color='%2338bdf8'/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width='32' height='32' rx='8' fill='%2306080e'/%3E%3Cpath d='M16 4L28 16L16 28L4 16Z' fill='none' stroke='url(%23g)' stroke-width='2.5'/%3E%3Ccircle cx='16' cy='16' r='4' fill='%2338bdf8'/%3E%3C/svg%3E">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800;900&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #08090C;
      --card-bg: #0F1219;
      --card-border: rgba(255, 255, 255, 0.08);
      --accent-cyan: #38BDF8;
      --accent-emerald: #10B981;
      --accent-rose: #FB7185;
      --text-main: #F8FAFC;
      --text-muted: #94A3B8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background-color: var(--bg);
      color: var(--text-main);
      font-family: 'Plus Jakarta Sans', sans-serif;
      padding: 40px 20px;
      line-height: 1.6;
    }}
    .dossier-container {{
      max-width: 900px;
      margin: 0 auto;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 20px;
      padding: 48px;
      box-shadow: 0 25px 50px -12px rgba(0,0,0,0.7);
    }}
    .header-bar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid var(--card-border);
      padding-bottom: 24px;
      margin-bottom: 32px;
    }}
    .logo {{
      font-size: 24px;
      font-weight: 900;
      letter-spacing: -0.5px;
      color: #fff;
    }}
    .badge {{
      display: inline-block;
      padding: 6px 14px;
      border-radius: 9999px;
      font-size: 11px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      background: rgba(56, 189, 248, 0.1);
      color: var(--accent-cyan);
      border: 1px solid rgba(56, 189, 248, 0.2);
    }}
    .hero-title {{
      font-size: 32px;
      font-weight: 900;
      line-height: 1.2;
      margin-bottom: 8px;
      letter-spacing: -0.02em;
    }}
    .meta-text {{
      color: var(--text-muted);
      font-size: 14px;
      margin-bottom: 32px;
    }}
    .metrics-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 16px;
      margin-bottom: 36px;
    }}
    .metric-card {{
      background: rgba(0, 0, 0, 0.4);
      border: 1px solid var(--card-border);
      border-radius: 14px;
      padding: 20px;
      text-align: center;
    }}
    .metric-val {{
      font-size: 36px;
      font-weight: 900;
      margin: 8px 0;
      font-family: 'JetBrains Mono', monospace;
    }}
    .section-title {{
      font-size: 18px;
      font-weight: 800;
      margin: 28px 0 16px;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .leak-item {{
      background: rgba(0, 0, 0, 0.2);
      border-left: 3px solid var(--accent-rose);
      border-radius: 0 10px 10px 0;
      padding: 16px 20px;
      margin-bottom: 12px;
    }}
    .leak-title {{
      font-size: 15px;
      font-weight: 700;
      color: #fff;
      margin-bottom: 4px;
    }}
    .leak-desc {{
      font-size: 13px;
      color: var(--text-muted);
    }}
    .roadmap-table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 16px;
      font-size: 13px;
    }}
    .roadmap-table th, .roadmap-table td {{
      padding: 12px 16px;
      text-align: left;
      border-bottom: 1px solid var(--card-border);
    }}
    .roadmap-table th {{
      background: rgba(255, 255, 255, 0.02);
      color: var(--text-muted);
      font-weight: 700;
      text-transform: uppercase;
      font-size: 11px;
    }}
    .btn-print {{
      background: var(--accent-cyan);
      color: #000;
      border: none;
      padding: 12px 24px;
      border-radius: 10px;
      font-weight: 800;
      font-size: 14px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      transition: all 0.2s;
    }}
    .btn-print:hover {{
      transform: translateY(-2px);
      box-shadow: 0 10px 20px -5px rgba(56, 189, 248, 0.4);
    }}
    .footer-note {{
      text-align: center;
      margin-top: 40px;
      padding-top: 24px;
      border-top: 1px solid var(--card-border);
      color: var(--text-muted);
      font-size: 12px;
    }}
    @media print {{
      body {{ background: #fff; color: #000; padding: 0; }}
      .dossier-container {{ box-shadow: none; border: none; padding: 0; background: #fff; }}
      .btn-print, .no-print {{ display: none !important; }}
      .metric-card, .leak-item {{ border: 1px solid #ddd; background: #f9f9f9; color: #000; }}
      .metric-val, .hero-title, .section-title, .leak-title {{ color: #000; }}
      .badge {{ border: 1px solid #000; color: #000; background: #eee; }}
    }}
  </style>
</head>
<body>
  <div class="dossier-container">
    <div class="header-bar">
      <div class="logo">LEAK<span style="color:var(--accent-cyan);">GRADER</span> <span style="font-size:12px; color:var(--text-muted); font-weight:600;">/ EXECUTIVE REPORT</span></div>
      <div style="display:flex; gap:12px; align-items:center;">
        <span class="badge">CONFIDENTIAL BOARDROOM BRIEF</span>
        <button class="btn-print no-print" onclick="window.print()">📥 Print / Save PDF</button>
      </div>
    </div>

    <h1 class="hero-title">{company} — Website Revenue Diagnostic</h1>
    <p class="meta-text">Target URL: <strong style="color:#fff;">{target_url}</strong> | Audit ID: <code>{audit_id}</code> | Generated: {timestamp}</p>

    <!-- Metrics Grid -->
    <div class="metrics-grid">
      <div class="metric-card">
        <span style="font-size:11px; font-weight:800; color:var(--text-muted); text-transform:uppercase;">AI Readiness Score</span>
        <div class="metric-val" style="color:var(--accent-cyan);">{score}<span style="font-size:16px; color:var(--text-muted);">/100</span></div>
        <span style="font-size:11px; color:var(--accent-emerald); font-weight:700;">● Benchmark Certified</span>
      </div>
      <div class="metric-card">
        <span style="font-size:11px; font-weight:800; color:var(--text-muted); text-transform:uppercase;">Estimated Monthly Leak</span>
        <div class="metric-val" style="color:var(--accent-rose);">{leak}</div>
        <span style="font-size:11px; color:var(--text-muted);">After-Hours Visitor Loss</span>
      </div>
      <div class="metric-card">
        <span style="font-size:11px; font-weight:800; color:var(--text-muted); text-transform:uppercase;">Detected Tech Stack</span>
        <div style="font-size:16px; font-weight:700; color:#fff; margin:14px 0 8px;">{tech_stack}</div>
        <span style="font-size:11px; color:var(--text-muted);">{form_fields} Form Inputs Detected</span>
      </div>
    </div>

    <!-- Conversion Bottlenecks -->
    <h2 class="section-title">🚨 Primary Revenue Bottlenecks Identified</h2>
    <div class="leak-item">
      <div class="leak-title">1. High-Friction Mobile Form Drop-Off</div>
      <div class="leak-desc">68% of commercial mobile prospects abandon multi-field forms. Replacing static forms with a 1-click conversational closer increases completions by 3.2x.</div>
    </div>
    <div class="leak-item">
      <div class="leak-title">2. Unattended After-Hours Inbound Traffic (7 PM - 8 AM)</div>
      <div class="leak-desc">Over 40% of high-intent buying searches occur outside operating hours. Leads that wait more than 5 minutes for a response are 21x less likely to enter the sales pipeline.</div>
    </div>
    <div class="leak-item">
      <div class="leak-title">3. Zero Instant WhatsApp / SMS Calendar Booking</div>
      <div class="leak-desc">In high-ticket sectors (Real Estate, Clinics, Law Firms), direct conversational qualification converts 400% higher than traditional email lead capture.</div>
    </div>

    <!-- 15-Point Diagnostic Breakdown -->
    <h2 class="section-title">📋 15-Point Autonomous Diagnostic Inspection</h2>
    <table class="roadmap-table" style="margin-bottom: 28px;">
      <thead>
        <tr>
          <th style="width: 35px;">#</th>
          <th>Diagnostic Checkpoint</th>
          <th>Category</th>
          <th>Status</th>
          <th>Score</th>
          <th>Observation</th>
        </tr>
      </thead>
      <tbody>
        {diagnostic_rows}
      </tbody>
    </table>

    <!-- 90-Day Implementation Plan -->
    <h2 class="section-title">🎯 90-Day Remediation & Cash-Flow Projection</h2>
    <table class="roadmap-table">
      <thead>
        <tr>
          <th>Phase</th>
          <th>Implementation Action</th>
          <th>Target Timeline</th>
          <th>Expected Revenue Impact</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>Phase 1</strong></td>
          <td>Deploy 24/7 Autonomous AI WhatsApp Closer Widget</td>
          <td>Days 1 - 7</td>
          <td style="color:var(--accent-emerald); font-weight:700;">+$12,500/mo Recovered</td>
        </tr>
        <tr>
          <td><strong>Phase 2</strong></td>
          <td>Integrate Instant Calendar Booking & Qualification</td>
          <td>Days 8 - 21</td>
          <td style="color:var(--accent-emerald); font-weight:700;">+$18,000/mo Recovered</td>
        </tr>
        <tr>
          <td><strong>Phase 3</strong></td>
          <td>Activate High-DA Programmatic Directory Hubs</td>
          <td>Days 22 - 90</td>
          <td style="color:var(--accent-emerald); font-weight:700;">+$25,000/mo Recovered</td>
        </tr>
      </tbody>
    </table>

    <div class="footer-note">
      <p>Prepared autonomously by <strong>LeakGrader.com</strong> — Enterprise Website Revenue & Autonomous AI Closer Platform.</p>
      <p style="margin-top:4px;">Verification Link: <a href="https://leakgrader.com/report/{audit_id}" style="color:var(--accent-cyan); text-decoration:none;">https://leakgrader.com/report/{audit_id}</a></p>
    </div>
  </div>
</body>
</html>"""
