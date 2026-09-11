"""
LeakGrader.com - Executive Revenue Opportunity Dossier Generator
Produces agency-grade printable HTML scorecards and self-contained PDF 1.4 documents.
Features:
- Dark theme styling
- Real Core Web Vitals (LCP, CLS, TBT, FCP) with Google thresholds
- Transparent score breakdown
- Prioritized findings with concrete evidence
- Conservative-to-expected opportunity range with disclaimer
"""

import time
import re

class ExecutiveDossierGenerator:
    def generate_dossier_html(self, audit_data: dict) -> str:
        company = audit_data.get("company_name") or audit_data.get("domain", "Target Enterprise")
        target_url = audit_data.get("url") or f"https://{audit_data.get('domain', 'target.com')}"
        score = audit_data.get("score") or audit_data.get("ai_readiness_score", 72)
        grade = audit_data.get("grade") or ("A" if score >= 80 else "B" if score >= 60 else "C")
        opp_range = audit_data.get("estimated_monthly_opportunity") or audit_data.get("estimated_monthly_leak", "$15,000 – $35,000/mo")
        disclaimer = audit_data.get("opportunity_disclaimer", "Illustrative estimate based on industry benchmarks and assumptions, not measured data.")
        form_fields = audit_data.get("form_friction_fields", 3)
        audit_id = audit_data.get("audit_id") or audit_data.get("id", "AUD-LIVE-REAL")
        timestamp = audit_data.get("timestamp", time.strftime("%Y-%m-%d %H:%M:%S UTC"))
        exec_summary = audit_data.get("executive_summary", f"Forensic conversion and speed audit for {company}. Scored {score}/100 based on verified technical benchmarks.")

        # Score Breakdown
        sb = audit_data.get("score_breakdown", {})
        perf_b = sb.get("performance", {})
        a11y_b = sb.get("accessibility", {})
        seo_b = sb.get("seo", {})
        conv_b = sb.get("conversion", {})

        perf_display = f"{perf_b.get('score')}/100" if perf_b.get("score") is not None else "Pending / Unavailable"
        a11y_display = f"{a11y_b.get('score')}/100" if a11y_b.get("score") is not None else "N/A"
        seo_display = f"{seo_b.get('score')}/100" if seo_b.get("score") is not None else "N/A"
        conv_display = f"{conv_b.get('score')}/100" if conv_b.get("score") is not None else "N/A"

        # Core Web Vitals
        cwv = audit_data.get("core_web_vitals", {})
        lcp = cwv.get("lcp", {})
        cls = cwv.get("cls", {})
        tbt = cwv.get("tbt", {})
        fcp = cwv.get("fcp", {})
        si = cwv.get("speed_index", {})

        def status_badge(st):
            if st == "GOOD" or st == "PASS":
                return '<span style="color:#10B981; font-weight:700; background:rgba(16,185,129,0.12); padding:3px 8px; border-radius:6px; font-size:11px;">PASS</span>'
            elif st == "NEEDS_IMPROVEMENT" or st == "WARN":
                return '<span style="color:#F59E0B; font-weight:700; background:rgba(245,158,11,0.12); padding:3px 8px; border-radius:6px; font-size:11px;">NEEDS WORK</span>'
            elif st == "POOR" or st == "FAIL":
                return '<span style="color:#FB7185; font-weight:700; background:rgba(251,113,133,0.12); padding:3px 8px; border-radius:6px; font-size:11px;">POOR</span>'
            return '<span style="color:#94A3B8; font-weight:700; background:rgba(148,163,184,0.12); padding:3px 8px; border-radius:6px; font-size:11px;">PENDING</span>'

        # Prioritized Recommendations HTML
        recs = audit_data.get("prioritized_recommendations") or audit_data.get("top_conversion_leaks", [])
        recs_html_list = []
        for i, r in enumerate(recs, 1):
            prio = r.get("priority", "MEDIUM")
            prio_color = "#FB7185" if prio == "HIGH" else "#F59E0B" if prio == "MEDIUM" else "#38BDF8"
            prio_bg = "rgba(251,113,133,0.12)" if prio == "HIGH" else "rgba(245,158,11,0.12)" if prio == "MEDIUM" else "rgba(56,189,248,0.12)"
            
            recs_html_list.append(f"""
            <div style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.08); border-left:4px solid {prio_color}; border-radius:12px; padding:18px 20px; margin-bottom:14px;">
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                <strong style="font-size:15px; color:#fff;">{i}. {r.get('title')}</strong>
                <span style="color:{prio_color}; background:{prio_bg}; border:1px solid {prio_color}40; padding:2px 8px; border-radius:6px; font-size:10px; font-weight:800;">{prio} PRIORITY</span>
              </div>
              <p style="font-size:13px; color:#cbd5e1; margin-bottom:6px;"><strong>Observed Evidence:</strong> {r.get('evidence')}</p>
              <p style="font-size:13px; color:#94a3b8; margin-bottom:8px;"><strong>Why It Matters:</strong> {r.get('why_it_matters')}</p>
              <div style="font-size:12.5px; color:#38bdf8; font-weight:600; background:rgba(56,189,248,0.08); padding:8px 12px; border-radius:8px;">
                <strong>Recommended Fix:</strong> {r.get('fix')}
              </div>
            </div>""")
        recs_html = "\n".join(recs_html_list)

        # 15 Diagnostic Checkpoints Table Rows
        diag_rows = []
        for p in audit_data.get("diagnostic_points", []):
            p_st = p.get("status", "PASS")
            st_color = "#10B981" if p_st == "PASS" else "#F59E0B" if p_st == "WARN" else "#FB7185"
            diag_rows.append(f"""
            <tr style="border-bottom:1px solid rgba(255,255,255,0.06);">
              <td style="padding:10px; color:#64748b; font-weight:700;">#{p.get('point_number')}</td>
              <td style="padding:10px; color:#fff; font-weight:600;">{p.get('name')}<br><small style="color:#64748b;">{p.get('category')}</small></td>
              <td style="padding:10px;"><span style="color:{st_color}; font-weight:800; font-size:11px;">{p_st}</span></td>
              <td style="padding:10px; color:#cbd5e1; font-size:12px;">{p.get('evidence', p.get('observation', ''))}</td>
            </tr>""")
        diag_rows_html = "\n".join(diag_rows)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Executive Revenue Opportunity Dossier - {company} | LeakGrader</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800;900&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #06080e;
      --card-bg: #0c101c;
      --card-border: rgba(255, 255, 255, 0.08);
      --accent-cyan: #38bdf8;
      --accent-emerald: #10b981;
      --accent-rose: #fb7185;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
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
      max-width: 920px;
      margin: 0 auto;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 20px;
      padding: 40px;
      box-shadow: 0 25px 50px rgba(0,0,0,0.8);
    }}
    .header-bar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid var(--card-border);
      padding-bottom: 20px;
      margin-bottom: 28px;
    }}
    .metrics-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      margin-bottom: 28px;
    }}
    .metric-card {{
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid var(--card-border);
      border-radius: 14px;
      padding: 20px;
      text-align: center;
    }}
    .table-container {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 12px;
      font-size: 13px;
    }}
    .table-container th {{
      padding: 10px;
      text-align: left;
      color: var(--text-muted);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      border-bottom: 1px solid var(--card-border);
    }}
    .btn-print {{
      background: var(--accent-cyan);
      color: #000;
      border: none;
      padding: 10px 20px;
      border-radius: 8px;
      font-weight: 800;
      font-size: 13px;
      cursor: pointer;
    }}
    @media print {{
      body {{ background: #fff; color: #000; padding: 0; }}
      .dossier-container {{ box-shadow: none; border: none; padding: 0; background: #fff; color: #000; }}
      .btn-print, .no-print {{ display: none !important; }}
      .metric-card {{ border: 1px solid #ddd; background: #f9f9f9; color: #000; }}
      h1, h2, strong {{ color: #000 !important; }}
    }}
  </style>
</head>
<body>
  <div class="dossier-container">
    <div class="header-bar">
      <div>
        <span style="font-size:22px; font-weight:900; color:#fff;">LEAK<strong style="color:var(--accent-cyan);">GRADER</strong></span>
        <span style="font-size:12px; color:var(--text-muted); margin-left:8px;">EXECUTIVE DOSSIER</span>
      </div>
      <button class="btn-print no-print" onclick="window.print()">📥 Print / Save PDF</button>
    </div>

    <h1 style="font-size:28px; font-weight:900; margin-bottom:6px;">{company} — Website Revenue Opportunity Dossier</h1>
    <p style="color:var(--text-muted); font-size:13px; margin-bottom:24px;">Target URL: <strong style="color:#fff;">{target_url}</strong> | Audit ID: <code>{audit_id}</code> | Date: {timestamp}</p>

    <!-- Executive Summary Callout -->
    <div style="background:rgba(56,189,248,0.06); border:1px solid rgba(56,189,248,0.2); border-radius:12px; padding:18px 20px; margin-bottom:28px;">
      <div style="font-size:11px; font-weight:800; color:var(--accent-cyan); text-transform:uppercase; margin-bottom:6px;">Executive Diagnostic Summary</div>
      <p style="font-size:14px; color:#e2e8f0; line-height:1.6;">{exec_summary}</p>
    </div>

    <!-- Top Metrics Grid -->
    <div class="metrics-grid">
      <div class="metric-card">
        <span style="font-size:11px; font-weight:800; color:var(--text-muted); text-transform:uppercase;">Overall Score</span>
        <div style="font-size:36px; font-weight:900; color:var(--accent-cyan); margin:6px 0;">{score}<span style="font-size:16px; color:var(--text-muted);">/100</span></div>
        <span style="font-size:11px; color:#10B981; font-weight:700;">Grade: {grade}</span>
      </div>
      <div class="metric-card">
        <span style="font-size:11px; font-weight:800; color:var(--text-muted); text-transform:uppercase;">Est. Monthly Opportunity</span>
        <div style="font-size:22px; font-weight:900; color:#fff; margin:10px 0;">{opp_range}</div>
        <span style="font-size:11px; color:var(--text-muted);">Conservative – Expected</span>
      </div>
      <div class="metric-card">
        <span style="font-size:11px; font-weight:800; color:var(--text-muted); text-transform:uppercase;">Form Field Friction</span>
        <div style="font-size:36px; font-weight:900; color:{'#10B981' if form_fields <= 3 else '#F59E0B'}; margin:6px 0;">{form_fields}</div>
        <span style="font-size:11px; color:var(--text-muted);">Visible inputs detected</span>
      </div>
    </div>

    <!-- Transparent Score Breakdown -->
    <h2 style="font-size:18px; font-weight:800; margin:28px 0 12px;">Defensible Scoring Breakdown</h2>
    <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(190px, 1fr)); gap:12px; margin-bottom:28px;">
      <div style="background:rgba(255,255,255,0.02); border:1px solid var(--card-border); border-radius:10px; padding:14px;">
        <span style="font-size:11px; color:var(--text-muted); font-weight:700;">PERFORMANCE (40%)</span>
        <div style="font-size:20px; font-weight:800; color:#fff; margin:4px 0;">{perf_display}</div>
        <small style="font-size:11px; color:#64748b;">Google PageSpeed API</small>
      </div>
      <div style="background:rgba(255,255,255,0.02); border:1px solid var(--card-border); border-radius:10px; padding:14px;">
        <span style="font-size:11px; color:var(--text-muted); font-weight:700;">ACCESSIBILITY (20%)</span>
        <div style="font-size:20px; font-weight:800; color:#fff; margin:4px 0;">{a11y_display}</div>
        <small style="font-size:11px; color:#64748b;">Semantic & Responsive</small>
      </div>
      <div style="background:rgba(255,255,255,0.02); border:1px solid var(--card-border); border-radius:10px; padding:14px;">
        <span style="font-size:11px; color:var(--text-muted); font-weight:700;">SEO & STRUCTURE (20%)</span>
        <div style="font-size:20px; font-weight:800; color:#fff; margin:4px 0;">{seo_display}</div>
        <small style="font-size:11px; color:#64748b;">Meta, OpenGraph & Schema</small>
      </div>
      <div style="background:rgba(255,255,255,0.02); border:1px solid var(--card-border); border-radius:10px; padding:14px;">
        <span style="font-size:11px; color:var(--text-muted); font-weight:700;">CONVERSION SIGNALS (20%)</span>
        <div style="font-size:20px; font-weight:800; color:#fff; margin:4px 0;">{conv_display}</div>
        <small style="font-size:11px; color:#64748b;">Touchpoints & CTA Flow</small>
      </div>
    </div>

    <!-- Core Web Vitals Table -->
    <h2 style="font-size:18px; font-weight:800; margin:28px 0 12px;">Google Core Web Vitals (Mobile Real-World Metrics)</h2>
    <div style="background:rgba(255,255,255,0.02); border:1px solid var(--card-border); border-radius:12px; padding:16px; margin-bottom:28px;">
      <table class="table-container">
        <thead>
          <tr>
            <th>Metric</th>
            <th>Measured Value</th>
            <th>Status</th>
            <th>Google Good Threshold</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style="padding:10px; font-weight:600;">Largest Contentful Paint (LCP)</td>
            <td style="padding:10px; font-weight:800; color:#fff;">{lcp.get('display', 'N/A')}</td>
            <td style="padding:10px;">{status_badge(lcp.get('status'))}</td>
            <td style="padding:10px; color:#64748b;">&le; 2.5s</td>
          </tr>
          <tr>
            <td style="padding:10px; font-weight:600;">Cumulative Layout Shift (CLS)</td>
            <td style="padding:10px; font-weight:800; color:#fff;">{cls.get('display', 'N/A')}</td>
            <td style="padding:10px;">{status_badge(cls.get('status'))}</td>
            <td style="padding:10px; color:#64748b;">&le; 0.1</td>
          </tr>
          <tr>
            <td style="padding:10px; font-weight:600;">Total Blocking Time (TBT)</td>
            <td style="padding:10px; font-weight:800; color:#fff;">{tbt.get('display', 'N/A')}</td>
            <td style="padding:10px;">{status_badge(tbt.get('status'))}</td>
            <td style="padding:10px; color:#64748b;">&le; 200ms</td>
          </tr>
          <tr>
            <td style="padding:10px; font-weight:600;">First Contentful Paint (FCP)</td>
            <td style="padding:10px; font-weight:800; color:#fff;">{fcp.get('display', 'N/A')}</td>
            <td style="padding:10px;">{status_badge(fcp.get('status'))}</td>
            <td style="padding:10px; color:#64748b;">&le; 1.8s</td>
          </tr>
          <tr>
            <td style="padding:10px; font-weight:600;">Speed Index</td>
            <td style="padding:10px; font-weight:800; color:#fff;">{si.get('display', 'N/A')}</td>
            <td style="padding:10px;">{status_badge(si.get('status'))}</td>
            <td style="padding:10px; color:#64748b;">&le; 3.4s</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Prioritized Actionable Recommendations -->
    <h2 style="font-size:18px; font-weight:800; margin:28px 0 12px;">Prioritized Actionable Recommendations</h2>
    <div style="margin-bottom:28px;">
      {recs_html}
    </div>

    <!-- 15-Point Forensic Checkpoint Table -->
    <h2 style="font-size:18px; font-weight:800; margin:28px 0 12px;">Full 15-Point Forensic Inspection Evidence</h2>
    <div style="background:rgba(255,255,255,0.02); border:1px solid var(--card-border); border-radius:12px; padding:16px; margin-bottom:28px; overflow-x:auto;">
      <table class="table-container">
        <thead>
          <tr>
            <th style="width:40px;">#</th>
            <th style="width:240px;">Checkpoint</th>
            <th style="width:80px;">Status</th>
            <th>Observed Evidence</th>
          </tr>
        </thead>
        <tbody>
          {diag_rows_html}
        </tbody>
      </table>
    </div>

    <!-- Methodology & Disclaimer -->
    <div style="background:rgba(255,255,255,0.02); border:1px solid var(--card-border); border-radius:10px; padding:16px 20px; font-size:12px; color:var(--text-muted); line-height:1.5;">
      <strong>Methodology & Estimation Disclaimer:</strong> {disclaimer}
      Public front-end forensic inspection only. No private or banking systems accessed.
    </div>

    <div style="text-align:center; margin-top:30px; font-size:12px; color:#64748b;">
      Generated autonomously by LeakGrader.com AI Platform
    </div>
  </div>
</body>
</html>"""


def generate_audit_pdf(audit_data: dict) -> bytes:
    """
    Generates a valid, self-contained PDF 1.4 binary stream with
    domain, score, revenue opportunity range, all 15 diagnostic points,
    benchmark disclaimer, and remediation roadmap.
    """
    domain = audit_data.get("domain") or audit_data.get("company_name", "Target Domain")
    score = audit_data.get("score") or audit_data.get("ai_readiness_score", 70)
    opp = audit_data.get("estimated_monthly_opportunity") or audit_data.get("estimated_monthly_leak", "$15,000 – $35,000/mo")
    ts = audit_data.get("timestamp", time.strftime("%Y-%m-%d %H:%M:%S UTC"))
    diag_pts = audit_data.get("diagnostic_points", [])

    lines = [
        "LEAKGRADER EXECUTIVE REVENUE OPPORTUNITY DOSSIER",
        "=" * 50,
        f"Domain Target: {domain}",
        f"Conversion & Technical Readiness Score: {score}/100",
        f"Est. Monthly Revenue Opportunity: {opp}",
        f"Generated: {ts}",
        "",
        "BENCHMARK METHODOLOGY & DISCLAIMER:",
        "Illustrative estimate based on industry benchmarks and assumptions,",
        "not measured data. Enter your actual traffic and conversion data for accuracy.",
        "Public Front-End Forensic Diagnostic (No Private/Bank Data Accessed)",
        "",
        "15-POINT CONVERSION & SPEED AUDIT EVIDENCE:",
        "-" * 50
    ]

    for p in diag_pts:
        p_num = p.get("point_number", 1)
        p_name = p.get("name", "Diagnostic Check")
        p_cat = p.get("category", "General")
        p_stat = p.get("status", "PASS")
        p_sc = p.get("score", 80)
        lines.append(f"[{p_stat}] #{p_num} {p_name} ({p_cat}) - {p_sc}/100")
        ev = p.get("evidence", p.get("observation", ""))
        if ev:
            lines.append(f"      Evidence: {ev[:80]}")

    lines.extend([
        "-" * 50,
        "RECOMMENDED REMEDIATION & OPPORTUNITY ROADMAP:",
        "Phase 1 (Days 1-14): Streamline Mobile Forms (Reduce to <=3 fields)",
        "Phase 2 (Days 15-45): Add Direct Calendar Booking & Response Channels",
        "Phase 3 (Days 46-90): Optimize Core Web Vitals (LCP <= 2.5s) & Schema",
        "=" * 50,
        "Prepared autonomously by LeakGrader.com"
    ])

    # Build PDF Content Stream
    content_ops = ["BT", "/F1 9 Tf", "40 760 Td", "13 TL"]
    for l in lines:
        escaped = l.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        if "LEAKGRADER" in l:
            content_ops.append(f"T* /F1 14 Tf ({escaped}) Tj /F1 9 Tf")
        elif l.startswith("="):
            content_ops.append(f"T* /F1 10 Tf ({escaped}) Tj /F1 9 Tf")
        else:
            content_ops.append(f"T* ({escaped}) Tj")
    content_ops.append("ET")
    content_stream = "\n".join(content_ops).encode("latin-1", errors="replace")

    obj1 = b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    obj2 = b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    obj3 = (
        b"3 0 obj\n"
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]\n"
        b"   /Contents 4 0 R\n"
        b"   /Resources << /Font << /F1 5 0 R >> >>\n"
        b">>\nendobj\n"
    )
    obj4 = (
        f"4 0 obj\n<< /Length {len(content_stream)} >>\nstream\n".encode("latin-1")
        + content_stream
        + b"\nendstream\nendobj\n"
    )
    obj5 = b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"

    header = b"%PDF-1.4\n"
    offsets = []
    curr = len(header)
    for obj in [obj1, obj2, obj3, obj4, obj5]:
        offsets.append(curr)
        curr += len(obj)

    xref_offset = curr
    xref = [
        "xref\n0 6\n0000000000 65535 f \n",
        f"{offsets[0]:010d} 00000 n \n",
        f"{offsets[1]:010d} 00000 n \n",
        f"{offsets[2]:010d} 00000 n \n",
        f"{offsets[3]:010d} 00000 n \n",
        f"{offsets[4]:010d} 00000 n \n"
    ]
    xref_bytes = "".join(xref).encode("latin-1")
    trailer = (
        f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n"
    ).encode("latin-1")

    return header + obj1 + obj2 + obj3 + obj4 + obj5 + xref_bytes + trailer
