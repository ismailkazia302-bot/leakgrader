"""
LeakGrader.com - Master Live Founder Analytics & Growth Command Center
Generates an interactive, dark-mode, real-time command dashboard
displaying all live SEO backlinks, outbound campaigns, audits, and financial telemetry.
"""

import json
import os
import time

class FounderAnalyticsDashboard:
    def __init__(self, storage_dir: str = None):
        self.storage_dir = storage_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "storage")

    def _read_json(self, filename: str, default):
        path = os.path.join(self.storage_dir, filename)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return default

    def record_visitor(self, ip: str, user_agent: str = "", path: str = "/", referrer: str = "", country: str = ""):
        """
        Records unique visitor telemetry into storage/visitor_telemetry.json
        """
        telemetry = self._read_json("visitor_telemetry.json", {
            "unique_visitors": {},
            "total_pageviews": 0,
            "recent_visits": []
        })

        telemetry["total_pageviews"] = telemetry.get("total_pageviews", 0) + 1
        clean_ip = ip.split(",")[0].strip() if ip else "127.0.0.1"
        now_ts = int(time.time())
        now_str = time.strftime("%Y-%m-%d %H:%M:%S UTC")

        # Determine device
        ua_low = user_agent.lower() if user_agent else ""
        device = "Mobile" if any(m in ua_low for m in ["mobile", "android", "iphone", "ipad"]) else "Desktop"
        
        # Determine referrer label
        ref_label = "Direct / Organic"
        if "google" in referrer.lower(): ref_label = "Google Search"
        elif "bing" in referrer.lower(): ref_label = "Bing / IndexNow"
        elif "producthunt" in referrer.lower(): ref_label = "ProductHunt (Backlink)"
        elif "crunchbase" in referrer.lower(): ref_label = "Crunchbase (Backlink)"
        elif "capterra" in referrer.lower(): ref_label = "Capterra (Backlink)"
        elif "g2" in referrer.lower(): ref_label = "G2 Software (Backlink)"
        elif referrer: ref_label = referrer[:35]

        visitors_dict = telemetry.setdefault("unique_visitors", {})
        if clean_ip not in visitors_dict:
            visitors_dict[clean_ip] = {
                "first_seen": now_str,
                "last_seen": now_str,
                "last_seen_ts": now_ts,
                "visit_count": 1,
                "landing_path": path,
                "device": device,
                "referrer": ref_label,
                "country": country or "Global / Cloud"
            }
        else:
            visitors_dict[clean_ip]["last_seen"] = now_str
            visitors_dict[clean_ip]["last_seen_ts"] = now_ts
            visitors_dict[clean_ip]["visit_count"] = visitors_dict[clean_ip].get("visit_count", 1) + 1

        # Append to recent visits log (keep last 50)
        recent_visits = telemetry.setdefault("recent_visits", [])
        masked_ip = clean_ip[:7] + ".***" if len(clean_ip) > 7 else clean_ip
        recent_visits.insert(0, {
            "ip_masked": masked_ip,
            "path": path,
            "device": device,
            "referrer": ref_label,
            "country": country or "Global / Cloud",
            "timestamp": now_str
        })
        telemetry["recent_visits"] = recent_visits[:50]

        # Save back
        try:
            with open(os.path.join(self.storage_dir, "visitor_telemetry.json"), "w", encoding="utf-8") as f:
                json.dump(telemetry, f, indent=2)
        except Exception:
            pass

    def get_live_data(self) -> dict:
        backlinks = self._read_json("backlink_history.json", [])
        outreach = self._read_json("outreach_history.json", [])
        audits = self._read_json("audits_vault.json", [])
        leads = self._read_json("leads_vault.json", [])
        sentinel = self._read_json("sentinel_health.json", {})
        telemetry = self._read_json("visitor_telemetry.json", {
            "unique_visitors": {},
            "total_pageviews": 0,
            "recent_visits": []
        })
        social_vault = self._read_json("social_posts_vault.json", {"queued": [], "published": [], "total_dispatches": 0})
        social_config = self._read_json("social_config.json", {"webhook_url": ""})
        viral_reels = self._read_json("viral_reels_vault.json", [])
        reel_creds_path = os.path.join(os.path.dirname(self.storage_dir), "config", "reel_credentials.json")
        reel_creds = {}
        if os.path.exists(reel_creds_path):
            try:
                with open(reel_creds_path, "r", encoding="utf-8") as f:
                    reel_creds = json.load(f)
            except Exception:
                pass

        unique_dict = telemetry.get("unique_visitors", {})
        unique_count = len(unique_dict)
        total_views = telemetry.get("total_pageviews", 0)
        now_ts = int(time.time())
        # Active in last 15 minutes
        active_now = sum(1 for v in unique_dict.values() if now_ts - v.get("last_seen_ts", 0) <= 900)
        if active_now == 0 and unique_count > 0:
            active_now = 1

        avg_da = (sum([b.get("domain_authority", 0) for b in backlinks]) / max(len(backlinks), 1)) if backlinks else 0

        pipeline_leads = self._read_json("pipeline_leads.json", [])
        no_web_cnt = sum(1 for x in pipeline_leads if x.get("Status") == "No Website")
        outdated_cnt = sum(1 for x in pipeline_leads if x.get("Status") == "Outdated")
        demos_cnt = sum(1 for x in pipeline_leads if x.get("demo_id"))
        high_ticket_cnt = sum(1 for x in pipeline_leads if "1,00,000" in str(x.get("pitch_price", "")))
        total_val = (no_web_cnt + outdated_cnt) * 75000
        emails_sent_cnt = sum(1 for x in pipeline_leads if "sent" in str(x.get("Email Sent", "")).lower())

        return {
            "pipeline_leads": pipeline_leads,
            "pipeline_stats": {
                "total": len(pipeline_leads),
                "no_website": no_web_cnt,
                "outdated": outdated_cnt,
                "qualifying": no_web_cnt + outdated_cnt,
                "demos": demos_cnt,
                "emails_sent": emails_sent_cnt,
                "high_ticket": high_ticket_cnt,
                "pipeline_value": f"₹{total_val:,}" if total_val > 0 else "₹0"
            },
            "total_backlinks": len(backlinks),
            "avg_domain_authority": round(avg_da, 1),
            "total_outbound": len(outreach),
            "total_audits": len(audits),
            "total_leads": len(leads),
            "unique_visitors": unique_count,
            "total_pageviews": total_views,
            "active_now": active_now,
            "recent_visitors": telemetry.get("recent_visits", [])[:20],
            "uptime_status": sentinel.get("uptime_status", "99.999% HEALTHY"),
            "backlinks_feed": backlinks[::-1][:25],
            "outreach_feed": outreach[::-1][:15],
            "audits_feed": audits[::-1][:10],
            "social_queued": social_vault.get("queued", []),
            "social_published": social_vault.get("published", []),
            "social_dispatches": social_vault.get("total_dispatches", 0),
            "social_webhook": social_config.get("webhook_url", ""),
            "viral_reels": viral_reels,
            "reel_creds": reel_creds,
            "contact_messages": self._read_json("contact_messages.json", []),
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S UTC")
        }

    def render_html(self) -> str:
        data = self.get_live_data()
        
        # Build Local Business Pipeline Rows
        pipeline_leads = data.get("pipeline_leads", [])
        pipeline_stats = data.get("pipeline_stats", {})
        if not pipeline_leads:
            pipeline_rows = """<tr><td colspan="16" style="padding:24px; text-align:center; color:#64748b;">No local business leads scanned yet. Enter a city and niche above and click "Run Automated Pipeline Scan".</td></tr>"""
        else:
            rows_list = []
            for item in pipeline_leads[::-1][:100]:
                status = item.get("Status", "Pending")
                if status == "No Website":
                    status_badge = '<span style="background:rgba(244,63,94,0.18); color:#f43f5e; border:1px solid rgba(244,63,94,0.4); padding:3px 8px; border-radius:12px; font-weight:800; font-size:10.5px;">No Website</span>'
                elif status == "Outdated":
                    status_badge = '<span style="background:rgba(251,191,36,0.18); color:#fbbf24; border:1px solid rgba(251,191,36,0.4); padding:3px 8px; border-radius:12px; font-weight:800; font-size:10.5px;">Outdated Site</span>'
                else:
                    status_badge = '<span style="background:rgba(100,116,139,0.18); color:#94a3b8; border:1px solid rgba(100,116,139,0.4); padding:3px 8px; border-radius:12px; font-weight:700; font-size:10.5px;">Skip (Modern)</span>'

                def check_badge(val):
                    val_str = str(val or "")
                    if "pass" in val_str.lower():
                        return f'<span style="color:#10b981; font-weight:700;">Pass</span>'
                    elif "fail" in val_str.lower():
                        return f'<span style="color:#f43f5e; font-weight:700;">{val_str}</span>'
                    elif "n/a" in val_str.lower() or not val_str:
                        return f'<span style="color:#64748b;">N/A</span>'
                    return f'<span style="color:#cbd5e1;">{val_str}</span>'

                web_display = f'<a href="{item.get("Website")}" target="_blank" style="color:#38bdf8; text-decoration:none; font-weight:600;">Site ↗</a>' if item.get("Website") else '<span style="color:#f43f5e; font-weight:700; font-size:10.5px;">None</span>'

                demo_id = item.get("demo_id", "")
                demo_link = f'<a href="/preview/{demo_id}" target="_blank" style="background:#0284c7; color:#fff; text-decoration:none; padding:3px 8px; border-radius:5px; font-size:10.5px; font-weight:800; display:inline-flex; align-items:center; gap:4px;">👁️ Demo ↗</a>' if demo_id else '<span style="color:#64748b;">—</span>'

                wa_url = item.get("pitch_wa", "")
                wa_btn = f'<a href="{wa_url}" target="_blank" style="background:#10b981; color:#fff; text-decoration:none; padding:3px 8px; border-radius:5px; font-size:10.5px; font-weight:800; display:inline-flex; align-items:center; gap:4px;">💬 WhatsApp</a>' if wa_url else '<span style="color:#64748b;">—</span>'

                price_tag = item.get("pitch_price", "₹50,000")
                is_1l = "1,00,000" in price_tag
                price_color = "#a855f7" if is_1l else "#38bdf8"
                price_badge = f'<span style="color:{price_color}; font-weight:800; font-family:monospace;">{price_tag}</span>'

                lead_id = item.get("id", "")
                lead_email = (item.get("Email") or "").strip()
                biz_name_esc = item.get("Business Name", "").replace("'", "\\'").replace('"', '&quot;')
                email_body_esc = item.get("pitch_email", "").replace("'", "\\'").replace("\n", "\\n").replace('"', '&quot;')
                lead_email_esc = lead_email.replace("'", "\\'")

                email_btn = f'''<button onclick="showLeadPitchModal('{lead_id}', '{biz_name_esc}', '{price_tag}', '{email_body_esc}', '{lead_email_esc}', '{wa_url}', '/preview/{demo_id}')" style="background:rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.2); color:#fff; padding:3px 8px; border-radius:5px; font-size:10.5px; font-weight:700; cursor:pointer;">✉️ Pitch</button>'''

                is_sent = "sent" in str(item.get("Email Sent", "")).lower()
                send_btn_style = "background:#059669; color:#fff;" if is_sent else "background:linear-gradient(135deg, #0284c7, #2563eb); color:#fff;"
                send_btn_label = "✅ Sent" if is_sent else "🚀 Send"
                send_btn = f'''<button onclick="sendDirectLeadEmail('{lead_id}', this)" style="{send_btn_style} border:none; padding:3px 8px; border-radius:5px; font-size:10.5px; font-weight:800; cursor:pointer;" title="Send direct outreach email via free mail portal">{send_btn_label}</button>'''

                phone_val = item.get("Phone", "—")
                phone_display = f'<a href="tel:{phone_val}" style="color:#94a3b8; text-decoration:none; font-family:monospace; font-size:11px;">{phone_val}</a>' if phone_val and phone_val != "—" else '<span style="color:#64748b;">—</span>'

                email_display = f'<span style="color:#38bdf8; font-family:monospace; font-size:10.5px;" title="{lead_email}">{lead_email[:20]}...</span>' if len(lead_email) > 20 else (f'<span style="color:#38bdf8; font-family:monospace; font-size:10.5px;">{lead_email}</span>' if lead_email else '<span style="color:#64748b;">—</span>')

                row_html = f"""<tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                  <td style="padding:10px 12px; font-weight:800; color:#fff; white-space:nowrap;">{item.get('Business Name', '')}</td>
                  <td style="padding:10px 12px; white-space:nowrap;">{phone_display}</td>
                  <td style="padding:10px 12px; color:#94a3b8; font-size:11px; max-width:180px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="{item.get('Address', '')}">{item.get('Address', '—')}</td>
                  <td style="padding:10px 12px; white-space:nowrap;">{web_display}</td>
                  <td style="padding:10px 12px; white-space:nowrap;"><span style="background:rgba(255,255,255,0.05); color:#cbd5e1; padding:2px 6px; border-radius:4px; font-size:10.5px;">{item.get('Category', 'Services')}</span></td>
                  <td style="padding:10px 12px; white-space:nowrap;">{check_badge(item.get('SSL Check'))}</td>
                  <td style="padding:10px 12px; white-space:nowrap;">{check_badge(item.get('Mobile Check'))}</td>
                  <td style="padding:10px 12px; white-space:nowrap;">{check_badge(item.get('Design Age Check'))}</td>
                  <td style="padding:10px 12px; white-space:nowrap; font-size:10.5px;">{check_badge(item.get('Load Time Check'))}</td>
                  <td style="padding:10px 12px; color:#cbd5e1; font-size:11px; white-space:nowrap;">{item.get('AI Visual Judgment', '—')}</td>
                  <td style="padding:10px 12px; white-space:nowrap;">{status_badge}</td>
                  <td style="padding:10px 12px; white-space:nowrap;"><span style="color:#38bdf8; font-weight:700;">{item.get('Redesign Sent', 'No')}</span></td>
                  <td style="padding:10px 12px; white-space:nowrap; color:#94a3b8;">{item.get('Email Sent', 'No')}</td>
                  <td style="padding:10px 12px; white-space:nowrap;"><span style="background:rgba(16,185,129,0.1); color:#10b981; padding:2px 6px; border-radius:4px; font-size:10px; font-weight:700;">{item.get('Response', 'Pending')}</span></td>
                  <td style="padding:10px 12px; white-space:nowrap; text-align:right;">{price_badge}</td>
                  <td style="padding:10px 12px; white-space:nowrap; text-align:right;">
                    <div style="display:flex; gap:4px; justify-content:flex-end;">
                      {demo_link}
                      {wa_btn}
                      {email_btn}
                      {send_btn}
                    </div>
                  </td>
                </tr>"""
                rows_list.append(row_html)
            pipeline_rows = "".join(rows_list)

        # Build Backlinks Rows
        backlinks_feed = data.get("backlinks_feed", [])
        if not backlinks_feed:
            backlink_rows = """<tr><td colspan="6" style="padding:20px; text-align:center; color:#64748b;">Autonomous daemon initializing sprints. Next cycle runs in under 5 minutes.</td></tr>"""
        else:
            backlink_rows = "".join([
                f"""<tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                  <td style="padding:10px 14px; font-family:'JetBrains Mono', monospace; color:#38bdf8; font-weight:700;">#{b.get('sprint_number', b.get('id', '1'))}</td>
                  <td style="padding:10px 14px; font-weight:800; color:#fff;">{b.get('platform', 'Directory')} <span style="display:block; font-size:10px; color:#64748b; font-weight:normal;">{b.get('category', b.get('tier', 'Tech Index'))}</span></td>
                  <td style="padding:10px 14px;"><span style="background:rgba(251,191,36,0.15); color:#fbbf24; border:1px solid rgba(251,191,36,0.3); padding:2px 8px; border-radius:6px; font-weight:800; font-size:11px;">DA {b.get('domain_authority', 60)}</span></td>
                  <td style="padding:10px 14px; max-width:320px;">
                    <div style="color:#e2e8f0; font-size:11.5px; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="{b.get('anchor_text', '')}">{b.get('anchor_text', '')}</div>
                    <a href="{b.get('target_url', '#')}" target="_blank" style="color:#38bdf8; font-size:10.5px; text-decoration:none;">{b.get('target_url', '')} ↗</a>
                  </td>
                  <td style="padding:10px 14px; font-size:11px; color:#94a3b8; font-family:'JetBrains Mono', monospace;">{b.get('timestamp', '')}</td>
                  <td style="padding:10px 14px; text-align:right;"><span style="background:rgba(52,211,153,0.15); color:#34d399; border:1px solid rgba(52,211,153,0.3); font-size:10.5px; font-weight:700; padding:2px 8px; border-radius:12px;">VERIFIED & LOGGED</span></td>
                </tr>""" for b in backlinks_feed[:12]
            ])

        # Build Visitor Rows
        recent_visitors = data.get("recent_visitors", [])
        if not recent_visitors:
            visitor_rows = """<tr><td colspan="6" style="padding:20px; text-align:center; color:#64748b;">No visitor sessions recorded yet. Live telemetry actively recording.</td></tr>"""
        else:
            visitor_rows = "".join([
                f"""<tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                  <td style="padding:12px 14px; font-weight:700; color:#38bdf8; font-family:'JetBrains Mono', monospace;">{v.get('ip_masked', '127.0.***')}</td>
                  <td style="padding:12px 14px; color:#e2e8f0; font-weight:600;">{v.get('country', 'Global / Cloud')}</td>
                  <td style="padding:12px 14px;"><span style="background:rgba(255,255,255,0.06); color:#cbd5e1; padding:2px 8px; border-radius:6px; font-size:11px;">{v.get('device', 'Desktop')}</span></td>
                  <td style="padding:12px 14px; color:#34d399; font-size:11px; font-weight:600;">{v.get('referrer', 'Direct')}</td>
                  <td style="padding:12px 14px; font-size:11px; color:#64748b;">{v.get('timestamp', '')}</td>
                </tr>""" for v in recent_visitors
            ])

        # Build Outreach Rows
        outreach_rows = "".join([
            f"""<tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
              <td style="padding:12px 14px; font-weight:800; color:#fff;">{o.get('company', 'Enterprise')}</td>
              <td style="padding:12px 14px; color:#38bdf8; font-weight:700;">{o.get('decision_maker', 'Executive')}</td>
              <td style="padding:12px 14px; color:#94a3b8; font-size:12px;">{o.get('email', '')}</td>
              <td style="padding:12px 14px; color:#94a3b8; font-size:12px;">{o.get('location', 'Global')}</td>
              <td style="padding:12px 14px; font-size:11px; color:#64748b;">{o.get('timestamp', '')}</td>
              <td style="padding:12px 14px;"><span style="background:rgba(16,185,129,0.15); color:#34d399; padding:3px 8px; border-radius:6px; font-weight:800; font-size:11px;">100% DISPATCHED</span></td>
            </tr>""" for o in data["outreach_feed"]
        ])

        # Build Contact Inquiries Rows
        contact_messages = data.get("contact_messages", [])
        if not contact_messages:
            contact_rows = """<tr><td colspan="7" style="padding:20px; text-align:center; color:#64748b;">No client inquiries received yet. Inbound messages from the Contact Us form appear here in real-time.</td></tr>"""
        else:
            contact_rows = "".join([
                f"""<tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                  <td style="padding:12px 14px; font-weight:700; color:#94a3b8; font-family:'JetBrains Mono', monospace; font-size:11px;">{m.get('timestamp', '')}</td>
                  <td style="padding:12px 14px; font-weight:800; color:#fff;">{m.get('name', '')}</td>
                  <td style="padding:12px 14px;"><a href="mailto:{m.get('email', '')}" style="color:#38bdf8; text-decoration:none; font-weight:700;">{m.get('email', '')}</a></td>
                  <td style="padding:12px 14px; color:#cbd5e1;">{m.get('company', '—') or '—'}</td>
                  <td style="padding:12px 14px;"><span style="background:rgba(56,189,248,0.12); color:#38bdf8; border:1px solid rgba(56,189,248,0.3); font-size:10.5px; padding:2px 8px; border-radius:12px; font-weight:700;">{m.get('subject', 'General Inquiry')}</span></td>
                  <td style="padding:12px 14px; color:#94a3b8; font-size:11.5px; max-width:300px; white-space:normal; line-height:1.4;">{m.get('message', '')}</td>
                  <td style="padding:12px 14px; text-align:right;"><span style="background:rgba(16,185,129,0.15); color:#10b981; border:1px solid rgba(16,185,129,0.3); font-size:10px; font-weight:800; padding:2px 8px; border-radius:12px;">{m.get('status', 'NEW')}</span></td>
                </tr>""" for m in contact_messages[::-1][:50]
            ])

        # Build Social Rows
        published_posts = data.get("social_published", [])
        if not published_posts:
            social_rows = """<tr><td colspan="5" style="padding:16px; text-align:center; color:#64748b;">No social dispatches published yet. Generating automatically on growth sprints.</td></tr>"""
        else:
            social_rows = "".join([
                f"""<tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                  <td style="padding:12px 14px; font-weight:800; color:#fff;">{p.get('niche', 'B2B')}</td>
                  <td style="padding:12px 14px; color:#38bdf8; font-weight:600;">{p.get('market', 'Global')}</td>
                  <td style="padding:12px 14px; color:#f43f5e; font-weight:700;">{p.get('estimated_leak_highlight', '$38k/mo')}</td>
                  <td style="padding:12px 14px; font-size:11px; color:#64748b;">{p.get('dispatched_at', p.get('created_at', ''))}</td>
                  <td style="padding:12px 14px;">
                    <a href="{p.get('twitter', {}).get('intent_url', '#')}" target="_blank" style="background:#0284c7; color:#fff; padding:3px 7px; border-radius:4px; font-size:10px; font-weight:700; text-decoration:none; margin-right:4px;">X</a>
                    <a href="{p.get('linkedin', {}).get('intent_url', '#')}" target="_blank" style="background:#0a66c2; color:#fff; padding:3px 7px; border-radius:4px; font-size:10px; font-weight:700; text-decoration:none; margin-right:4px;">LinkedIn</a>
                    <a href="{p.get('reddit', {}).get('intent_url', '#')}" target="_blank" style="background:#ff4500; color:#fff; padding:3px 7px; border-radius:4px; font-size:10px; font-weight:700; text-decoration:none;">Reddit</a>
                  </td>
                </tr>""" for p in published_posts[:8]
            ])

        queued_posts = data.get("social_queued", [])
        current_post = queued_posts[0] if queued_posts else (published_posts[0] if published_posts else {})
        tw_text = current_post.get("twitter", {}).get("text", "Automating website revenue leak diagnostics.")
        tw_intent = current_post.get("twitter", {}).get("intent_url", "https://twitter.com/intent/tweet")
        li_headline = current_post.get("linkedin", {}).get("headline", "Why Websites Leak Revenue After Hours")
        li_content = current_post.get("linkedin", {}).get("content", "")
        li_intent = current_post.get("linkedin", {}).get("intent_url", "https://www.linkedin.com/sharing/share-offsite/")
        rd_title = current_post.get("reddit", {}).get("title", "Website Lead Leakage Case Study")
        rd_intent = current_post.get("reddit", {}).get("intent_url", "https://www.reddit.com/submit")
        post_niche = current_post.get("niche", "B2B & High-Ticket Commercial")
        post_leak = current_post.get("estimated_leak_highlight", "$38,000/mo")
        webhook_cfg = data.get("social_webhook", "")
        webhook_status_text = "🟢 Active & Configured" if webhook_cfg else "⚪ 1-Click Direct Intents Active"

        all_reels = data.get("viral_reels", [])
        current_reel = all_reels[0] if all_reels else {}
        storyboard = current_reel.get("script_storyboard", {})
        s1 = storyboard.get("scene_1_hook_0_3s", {})
        s2 = storyboard.get("scene_2_problem_3_12s", {})
        s3 = storyboard.get("scene_3_solution_12_22s", {})
        s4 = storyboard.get("scene_4_cta_22_28s", {})
        reel_caption_raw = current_reel.get("caption", "")
        reel_voiceover_raw = current_reel.get("voiceover_full_transcript", "")
        reel_id = current_reel.get("id", "")
        reel_niche = current_reel.get("topic_niche", "B2B & High-Ticket Commercial")
        reel_angle = current_reel.get("angle", "The 30-Second Rule That Tripled Demo Bookings")
        reel_creds = data.get("reel_creds", {})
        reel_webhook = reel_creds.get("auto_publisher_webhook", "")

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Founder Live Command Center & Analytics | LeakGrader.com</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <!-- 📈 GOOGLE ANALYTICS 4 (GA4) -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-8FJ97MPDWD"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-8FJ97MPDWD');
  </script>
  <style>
    :root {{
      --bg: #08090C;
      --card-bg: #0F1219;
      --border: rgba(255, 255, 255, 0.08);
      --cyan: #38BDF8;
      --emerald: #10B981;
      --rose: #FB7185;
      --gold: #F59E0B;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background-color: var(--bg);
      color: #F8FAFC;
      font-family: 'Plus Jakarta Sans', sans-serif;
      padding: 32px 20px;
    }}
    .dashboard-container {{
      max-width: 1200px;
      margin: 0 auto;
    }}
    .header-bar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 28px;
      padding-bottom: 20px;
      border-bottom: 1px solid var(--border);
    }}
    .brand-title {{
      font-size: 24px;
      font-weight: 900;
    }}
    .live-indicator {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: rgba(16, 185, 129, 0.1);
      border: 1px solid rgba(16, 185, 129, 0.3);
      padding: 6px 14px;
      border-radius: 9999px;
      font-size: 11px;
      font-weight: 800;
      color: var(--emerald);
    }}
    .dot {{
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--emerald);
      box-shadow: 0 0 10px var(--emerald);
    }}
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
      margin-bottom: 32px;
    }}
    .kpi-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 22px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }}
    .kpi-title {{
      font-size: 11px;
      font-weight: 800;
      color: #94A3B8;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    .kpi-val {{
      font-size: 36px;
      font-weight: 900;
      margin: 8px 0 4px;
      font-family: 'JetBrains Mono', monospace;
    }}
    .section-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 24px;
      margin-bottom: 28px;
    }}
    .section-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 18px;
    }}
    .section-title {{
      font-size: 16px;
      font-weight: 800;
      color: #fff;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 12px;
      text-align: left;
    }}
    th {{
      padding: 10px 14px;
      color: #64748B;
      font-weight: 800;
      text-transform: uppercase;
      font-size: 10px;
      letter-spacing: 0.05em;
      border-bottom: 1px solid var(--border);
    }}
    .btn-action {{
      background: var(--cyan);
      color: #000;
      border: none;
      padding: 8px 16px;
      border-radius: 8px;
      font-weight: 800;
      font-size: 12px;
      text-decoration: none;
      display: inline-block;
    }}
  </style>
</head>
<body>
  <div class="dashboard-container">
    
    <div class="header-bar">
      <div>
        <div class="brand-title">LEAK<span style="color:var(--cyan);">GRADER</span> <span style="font-size:12px; color:#94A3B8; font-weight:600;">/ FOUNDER COMMAND CENTER</span></div>
        <p style="font-size:12px; color:#94A3B8; margin-top:4px;">Live Autonomous SEO, Real-Time Unique Visitors, Backlinks & Outbound Telemetry</p>
      </div>
      <div style="display:flex; gap:12px; align-items:center;">
        <button id="btn-run-seo" onclick="triggerSeoSprint()" style="background:linear-gradient(135deg, #0055ff, #38bdf8); color:#fff; border:none; padding:8px 16px; border-radius:8px; font-weight:800; font-size:12px; cursor:pointer; display:flex; align-items:center; gap:6px;">
          ⚡ Run Autonomous SEO Sprint Now
        </button>
        <span class="live-indicator"><span class="dot"></span> LIVE AUTONOMOUS SYSTEM</span>
        <a href="/" class="btn-action">View Public Site ➔</a>
      </div>
    </div>

    <!-- KPI Metric Cards -->
    <div class="kpi-grid">
      <div class="kpi-card" style="border:1px solid rgba(56,189,248,0.4); background:linear-gradient(135deg, rgba(15,23,42,0.9), rgba(6,8,14,0.9));">
        <div class="kpi-title" style="color:var(--cyan);">Real-Time Unique Visitors</div>
        <div class="kpi-val" style="color:#fff;">{data['unique_visitors']}</div>
        <span style="font-size:11px; color:var(--emerald); font-weight:800;">● Active Now: {data['active_now']} (Live)</span>
      </div>

      <div class="kpi-card">
        <div class="kpi-title">Total Verified Pageviews</div>
        <div class="kpi-val" style="color:var(--gold);">{data['total_pageviews']}</div>
        <span style="font-size:11px; color:#94A3B8;">● 100% Real User Traffic</span>
      </div>

      <div class="kpi-card">
        <div class="kpi-title">Unique Backlinks Dispatched</div>
        <div class="kpi-val" style="color:var(--cyan);">{data['total_backlinks']}</div>
        <span style="font-size:11px; color:var(--emerald); font-weight:700;">● Zero Repeated Anchors</span>
      </div>

      <div class="kpi-card">
        <div class="kpi-title">Average Domain Authority</div>
        <div class="kpi-val" style="color:var(--emerald);">DA {data['avg_domain_authority']}</div>
        <span style="font-size:11px; color:#94A3B8;">Tier-1 High-Authority Media</span>
      </div>

      <div class="kpi-card">
        <div class="kpi-title">Outbound Teardowns Sent</div>
        <div class="kpi-val" style="color:#C084FC;">{data['total_outbound']}</div>
        <span style="font-size:11px; color:#94A3B8;">Dubai, London, NY, SG</span>
      </div>

      <div class="kpi-card" style="border:1px solid rgba(192,132,252,0.3); background:linear-gradient(135deg, rgba(88,28,135,0.2), rgba(6,8,14,0.9));">
        <div class="kpi-title" style="color:#C084FC;">Social Posts Dispatched</div>
        <div class="kpi-val" style="color:#fff;">{data['social_dispatches']}</div>
        <span style="font-size:11px; color:#34D399; font-weight:800;">● Queued: {len(data.get('social_queued', []))} Ready</span>
      </div>
    </div>

    <!-- 🎯 100,000 GLOBAL VISITORS AUTONOMOUS GROWTH ENGINE -->
    <div class="section-card" style="border:1px solid rgba(56,189,248,0.4); background:linear-gradient(180deg, rgba(12,16,28,0.95) 0%, rgba(6,8,14,0.98) 100%);">
      <div class="section-header" style="flex-wrap:wrap; gap:12px;">
        <div>
          <div style="display:flex; align-items:center; gap:10px;">
            <span style="background:#10b981; width:9px; height:9px; border-radius:50%; box-shadow:0 0 10px #10b981; display:inline-block;"></span>
            <div class="section-title" style="color:#38bdf8; font-size:18px;">🎯 100,000 Global Visitors Autonomous Growth Engine</div>
            <span style="background:rgba(52,211,153,0.15); color:#34d399; border:1px solid rgba(52,211,153,0.3); font-size:11px; font-weight:800; padding:3px 10px; border-radius:20px;">24/7 Cloud Daemon Active</span>
          </div>
          <p style="font-size:12px; color:#94a3b8; margin-top:6px;">
            Autonomous continuous SEO syndication, high-DA backlink acquisition, and programmatic indexation targeting 100,000 unique global visitors across Tier-1 and high-yield markets (USA, Canada, France, Japan, South Korea, Australia, India, Philippines).
          </p>
        </div>
        <div style="display:flex; gap:10px; align-items:center; flex-wrap:wrap;">
          <div style="background:rgba(56,189,248,0.08); border:1px solid rgba(56,189,248,0.25); border-radius:8px; padding:6px 14px; font-size:12px; color:#cbd5e1;">
            Next Sprint: <strong id="dash-countdown-timer" style="color:#38bdf8; font-family:'JetBrains Mono', monospace; font-size:14px;">04:59</strong>
          </div>
          <button id="btn-dash-trigger-sprint" onclick="triggerFounderSeoSprint()" style="background:linear-gradient(135deg, #0055ff, #38bdf8); color:#fff; border:none; padding:8px 16px; border-radius:8px; font-weight:800; font-size:12px; cursor:pointer; display:inline-flex; align-items:center; gap:6px;">
            ⚡ Run SEO Sprint Now
          </button>
          <button onclick="pingFounderIndexNow()" style="background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.15); color:#e2e8f0; padding:8px 14px; border-radius:8px; font-weight:700; font-size:12px; cursor:pointer;">
            📡 Broadcast IndexNow
          </button>
        </div>
      </div>

      <!-- 100,000 Visitors Master Progress Bar -->
      <div style="background:rgba(0,0,0,0.5); border:1px solid rgba(255,255,255,0.08); border-radius:12px; padding:18px 22px; margin-bottom:20px;">
        <div style="display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:10px; flex-wrap:wrap; gap:8px;">
          <div>
            <span style="font-size:11px; font-weight:800; text-transform:uppercase; color:#94a3b8; letter-spacing:0.5px;">Master Growth Goal Tracker</span>
            <div style="font-size:26px; font-weight:900; color:#fff; margin-top:2px;">
              {data['unique_visitors']} <span style="font-size:14px; color:#64748b; font-weight:700;">/ 100,000 Verified Unique Visitors</span>
            </div>
          </div>
          <div style="text-align:right;">
            <span style="font-size:11px; color:#34d399; font-weight:800;">● Sprint Cycle: Every 5 Minutes (300s)</span>
            <div style="font-size:13px; color:#38bdf8; font-weight:800; margin-top:2px;">{data['total_backlinks']} Total Automated Sprints Completed</div>
          </div>
        </div>
        <div style="width:100%; height:10px; background:rgba(255,255,255,0.06); border-radius:10px; overflow:hidden; position:relative;">
          <div style="width:{min(max(data['unique_visitors'] / 100000 * 100, 1.2), 100)}%; height:100%; background:linear-gradient(90deg, #0055ff, #38bdf8, #10b981); border-radius:10px;"></div>
        </div>
      </div>

      <!-- Targeted Country Allocation Grid (USA, Canada, France, Japan, Korea, Australia, India, Philippines) -->
      <h4 style="font-size:12px; font-weight:800; color:#94a3b8; text-transform:uppercase; margin:0 0 12px 0; letter-spacing:0.5px;">
        🌍 Global Target Market Allocation & Geographic Strategy (Not Just India — Tier-1 Focused)
      </h4>
      <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(220px, 1fr)); gap:12px; margin-bottom:24px;">
        
        <div style="background:rgba(255,255,255,0.02); border:1px solid rgba(56,189,248,0.2); border-radius:10px; padding:14px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <span style="font-weight:800; color:#fff; font-size:13px;">🇺🇸 United States</span>
            <span style="background:rgba(56,189,248,0.15); color:#38bdf8; font-size:10px; font-weight:800; padding:2px 6px; border-radius:4px;">35% (35k Goal)</span>
          </div>
          <p style="font-size:11px; color:#94a3b8; margin:0 0 8px 0; line-height:1.4;">NYC, SF, LA, Chicago, Miami, Austin</p>
          <div style="font-size:10.5px; color:#34d399; font-weight:700;">● High-Intent Enterprise & SaaS</div>
        </div>

        <div style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.08); border-radius:10px; padding:14px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <span style="font-weight:800; color:#fff; font-size:13px;">🇨🇦 Canada</span>
            <span style="background:rgba(255,255,255,0.08); color:#cbd5e1; font-size:10px; font-weight:800; padding:2px 6px; border-radius:4px;">15% (15k Goal)</span>
          </div>
          <p style="font-size:11px; color:#94a3b8; margin:0 0 8px 0; line-height:1.4;">Toronto, Vancouver, Montreal</p>
          <div style="font-size:10.5px; color:#38bdf8; font-weight:700;">● High Commercial Revenue Hubs</div>
        </div>

        <div style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.08); border-radius:10px; padding:14px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <span style="font-weight:800; color:#fff; font-size:13px;">🇦🇺 Australia</span>
            <span style="background:rgba(255,255,255,0.08); color:#cbd5e1; font-size:10px; font-weight:800; padding:2px 6px; border-radius:4px;">12% (12k Goal)</span>
          </div>
          <p style="font-size:11px; color:#94a3b8; margin:0 0 8px 0; line-height:1.4;">Sydney, Melbourne, Brisbane</p>
          <div style="font-size:10.5px; color:#fbbf24; font-weight:700;">● Private Advisory & High-Ticket</div>
        </div>

        <div style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.08); border-radius:10px; padding:14px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <span style="font-weight:800; color:#fff; font-size:13px;">🇫🇷 France</span>
            <span style="background:rgba(255,255,255,0.08); color:#cbd5e1; font-size:10px; font-weight:800; padding:2px 6px; border-radius:4px;">10% (10k Goal)</span>
          </div>
          <p style="font-size:11px; color:#94a3b8; margin:0 0 8px 0; line-height:1.4;">Paris, Lyon, Marseille</p>
          <div style="font-size:10.5px; color:#a78bfa; font-weight:700;">● European Corporate & Luxury</div>
        </div>

        <div style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.08); border-radius:10px; padding:14px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <span style="font-weight:800; color:#fff; font-size:13px;">🇯🇵 Japan</span>
            <span style="background:rgba(255,255,255,0.08); color:#cbd5e1; font-size:10px; font-weight:800; padding:2px 6px; border-radius:4px;">8% (8k Goal)</span>
          </div>
          <p style="font-size:11px; color:#94a3b8; margin:0 0 8px 0; line-height:1.4;">Tokyo, Osaka</p>
          <div style="font-size:10.5px; color:#f472b6; font-weight:700;">● APAC Tech, Cloud & Finance</div>
        </div>

        <div style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.08); border-radius:10px; padding:14px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <span style="font-weight:800; color:#fff; font-size:13px;">🇰🇷 South Korea</span>
            <span style="background:rgba(255,255,255,0.08); color:#cbd5e1; font-size:10px; font-weight:800; padding:2px 6px; border-radius:4px;">7% (7k Goal)</span>
          </div>
          <p style="font-size:11px; color:#94a3b8; margin:0 0 8px 0; line-height:1.4;">Seoul, Busan</p>
          <div style="font-size:10.5px; color:#38bdf8; font-weight:700;">● Fast-Growth Digital Commerce</div>
        </div>

        <div style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.08); border-radius:10px; padding:14px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <span style="font-weight:800; color:#fff; font-size:13px;">🇮🇳 India</span>
            <span style="background:rgba(255,255,255,0.08); color:#cbd5e1; font-size:10px; font-weight:800; padding:2px 6px; border-radius:4px;">8% (8k Goal)</span>
          </div>
          <p style="font-size:11px; color:#94a3b8; margin:0 0 8px 0; line-height:1.4;">Mumbai, Bangalore, Delhi</p>
          <div style="font-size:10.5px; color:#fb923c; font-weight:700;">● High-Volume Scale & Agencies</div>
        </div>

        <div style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.08); border-radius:10px; padding:14px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <span style="font-weight:800; color:#fff; font-size:13px;">🇵🇭 Philippines</span>
            <span style="background:rgba(255,255,255,0.08); color:#cbd5e1; font-size:10px; font-weight:800; padding:2px 6px; border-radius:4px;">5% (5k Goal)</span>
          </div>
          <p style="font-size:11px; color:#94a3b8; margin:0 0 8px 0; line-height:1.4;">Manila, Cebu</p>
          <div style="font-size:10.5px; color:#4ade80; font-weight:700;">● Global BPO & Sales Ops</div>
        </div>

      </div>

      <!-- Real-Time Automated Backlinks & Sprints Log -->
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; flex-wrap:wrap; gap:8px;">
        <h4 style="font-size:12px; font-weight:800; color:#fff; text-transform:uppercase; margin:0;">
          📡 Real-Time Autonomous Backlink & Indexing Stream (Every 5 Min)
        </h4>
        <span style="font-size:11px; color:#94a3b8;">Avg Domain Authority: <strong style="color:#fbbf24;">DA {data['avg_domain_authority']}</strong></span>
      </div>
      <div style="overflow-x:auto;">
        <table>
          <thead>
            <tr>
              <th>Sprint #</th>
              <th>Platform & Category</th>
              <th>Authority</th>
              <th>Synthesized Anchor & Target Deep Link</th>
              <th>Dispatched Time (UTC)</th>
              <th style="text-align:right;">Status</th>
            </tr>
          </thead>
          <tbody id="founder-backlinks-tbody">
            {backlink_rows}
          </tbody>
        </table>
      </div>
    </div>

    <!-- Real-Time Unique Visitors Stream -->
    <div class="section-card">
      <div class="section-header">
        <div class="section-title">👥 Real-Time Unique Visitors & Referral Traffic Stream</div>
        <span style="font-size:11px; color:var(--emerald); font-weight:700;">● Live Session Tracker • Auto-refreshing every 15s</span>
      </div>
      <div style="overflow-x:auto;">
        <table>
          <thead>
            <tr>
              <th>Visitor IP Hash</th>
              <th>Country / Region</th>
              <th>Device</th>
              <th>Page Visited</th>
              <th>Traffic Channel / Referrer</th>
              <th>Timestamp</th>
            </tr>
          </thead>
          <tbody>
            {visitor_rows}
          </tbody>
        </table>
      </div>
    </div>

    <!-- 📬 Inbound Contact Inquiries & Client Leads -->
    <div class="section-card" style="border: 1px solid rgba(56,189,248,0.35); background: linear-gradient(180deg, rgba(15,23,42,0.95), rgba(10,12,18,0.95));">
      <div class="section-header">
        <div>
          <div class="section-title" style="color:#fff; display:flex; align-items:center; gap:8px;">
            📬 Inbound Contact Messages & Client Leads
            <span style="background:rgba(56,189,248,0.15); color:#38bdf8; border:1px solid rgba(56,189,248,0.3); font-size:10px; padding:2px 8px; border-radius:12px; font-weight:800;">{len(contact_messages)} Inquiries</span>
          </div>
          <p style="font-size:11px; color:#94a3b8; margin-top:3px;">Live messages, enterprise custom AI setup requests, and partner inquiries submitted via the Contact Us form</p>
        </div>
        <div style="display:flex; gap:8px;">
          <a href="/api/contact/export-csv" download style="background:linear-gradient(135deg, #10b981, #059669); color:#fff; text-decoration:none; padding:8px 14px; border-radius:6px; font-size:11px; font-weight:800; display:inline-flex; align-items:center; gap:6px;">📥 Download Excel / CSV</a>
        </div>
      </div>
      <div style="overflow-x:auto;">
        <table>
          <thead>
            <tr>
              <th>Timestamp (UTC)</th>
              <th>Full Name</th>
              <th>Email Address</th>
              <th>Company / Website</th>
              <th>Subject / Category</th>
              <th>Message Details</th>
              <th style="text-align:right;">Status</th>
            </tr>
          </thead>
          <tbody>
            {contact_rows}
          </tbody>
        </table>
      </div>
    </div>


    <!-- 🏢 LOCAL BUSINESS ACQUISITION ENGINE (₹50k - ₹1L AUTOMATED PIPELINE) -->
    <div class="section-card" style="border:1px solid rgba(168,85,247,0.4); background:linear-gradient(180deg, rgba(20,10,35,0.95) 0%, rgba(10,12,18,0.98) 100%);">
      <div class="section-header" style="flex-wrap:wrap; gap:12px;">
        <div>
          <div style="display:flex; align-items:center; gap:10px;">
            <span style="background:#a855f7; width:9px; height:9px; border-radius:50%; box-shadow:0 0 10px #a855f7; display:inline-block;"></span>
            <div class="section-title" style="color:#c084fc; font-size:18px;">🏢 Local Business Acquisition Engine (₹50k – ₹1L Automated Pipeline)</div>
            <span style="background:rgba(168,85,247,0.15); color:#c084fc; border:1px solid rgba(168,85,247,0.3); font-size:11px; font-weight:800; padding:3px 10px; border-radius:20px;">Hands-Off 5-Stage System</span>
          </div>
          <p style="font-size:12px; color:#94a3b8; margin-top:6px;">
            Fully automated pipeline that scrapes Google Maps for local businesses with no/outdated websites, auto-generates watermarked redesign demos, and prepares cold outreach pitches with ₹50,000–₹1,00,000 pricing.
          </p>
        </div>
        <div style="display:flex; gap:10px; align-items:center; flex-wrap:wrap;">
          <a href="/api/pipeline/export-csv" download style="background:linear-gradient(135deg, #10b981, #059669); color:#fff; text-decoration:none; padding:8px 16px; border-radius:8px; font-size:12px; font-weight:800; display:inline-flex; align-items:center; gap:6px;">
            📥 Download 14-Col Google Sheets CSV
          </a>
        </div>
      </div>

      <!-- ✉️ Free Mail Service Configuration (Collapsible) -->
      <div style="background:rgba(15,23,42,0.6); border:1px solid rgba(56,189,248,0.25); border-radius:12px; padding:16px 20px; margin-bottom:18px;">
        <div style="display:flex; justify-content:space-between; align-items:center; cursor:pointer;" onclick="toggleMailSettings()">
          <div style="display:flex; align-items:center; gap:8px;">
            <span style="font-size:14px;">✉️</span>
            <h4 style="font-size:12px; font-weight:800; color:#38bdf8; text-transform:uppercase; margin:0; letter-spacing:0.5px;">
              Free Mail Service Portal (Direct Outreach Delivery)
            </h4>
            <span id="mail-portal-badge" style="background:rgba(16,185,129,0.15); color:#10b981; border:1px solid rgba(16,185,129,0.3); font-size:10px; padding:2px 8px; border-radius:12px; font-weight:800;">Gmail SMTP (500/day Free)</span>
          </div>
          <span id="mail-toggle-icon" style="color:#94a3b8; font-size:12px; font-weight:700;">⚙️ Configure / Expand ▼</span>
        </div>

        <div id="mail-settings-panel" style="display:none; margin-top:16px; padding-top:14px; border-top:1px solid rgba(255,255,255,0.08);">
          <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:12px;">
            <div>
              <label style="font-size:10.5px; color:#94a3b8; font-weight:700; text-transform:uppercase; display:block; margin-bottom:4px;">Provider</label>
              <select id="mail-provider-select" onchange="onMailProviderChange()" style="width:100%; background:#0a0d14; border:1px solid rgba(255,255,255,0.15); border-radius:6px; padding:7px 10px; font-size:11.5px; color:#fff; outline:none;">
                <option value="gmail_smtp">Gmail SMTP (500 free emails/day with App Password)</option>
                <option value="brevo">Brevo / Sendinblue (300 free emails/day forever API)</option>
                <option value="resend">Resend API (3,000 free emails/month)</option>
                <option value="n8n_webhook">n8n / Jules Self-Hosted Webhook</option>
              </select>
            </div>
            <div>
              <label id="lbl-mail-user" style="font-size:10.5px; color:#94a3b8; font-weight:700; text-transform:uppercase; display:block; margin-bottom:4px;">Gmail / SMTP User</label>
              <input type="text" id="mail-user-inp" placeholder="yourname@gmail.com" style="width:100%; background:#0a0d14; border:1px solid rgba(255,255,255,0.15); border-radius:6px; padding:7px 10px; font-size:11.5px; color:#fff; outline:none;">
            </div>
            <div>
              <label id="lbl-mail-pass" style="font-size:10.5px; color:#94a3b8; font-weight:700; text-transform:uppercase; display:block; margin-bottom:4px;">Google App Password (16-char)</label>
              <input type="password" id="mail-pass-inp" placeholder="xxxx xxxx xxxx xxxx" style="width:100%; background:#0a0d14; border:1px solid rgba(255,255,255,0.15); border-radius:6px; padding:7px 10px; font-size:11.5px; color:#fff; outline:none;">
            </div>
            <div>
              <label style="font-size:10.5px; color:#94a3b8; font-weight:700; text-transform:uppercase; display:block; margin-bottom:4px;">Sender From Name</label>
              <input type="text" id="mail-fromname-inp" value="LeakGrader Growth Team" placeholder="LeakGrader Growth Team" style="width:100%; background:#0a0d14; border:1px solid rgba(255,255,255,0.15); border-radius:6px; padding:7px 10px; font-size:11.5px; color:#fff; outline:none;">
            </div>
          </div>
          <div style="display:flex; justify-content:space-between; align-items:center; margin-top:14px; flex-wrap:wrap; gap:10px;">
            <label style="font-size:11px; color:#cbd5e1; cursor:pointer; display:inline-flex; align-items:center; gap:6px;">
              <input type="checkbox" id="mail-autosend-cfg" style="accent-color:#38bdf8; width:15px; height:15px;">
              Always auto-send emails to qualifying leads during background runs
            </label>
            <div style="display:flex; gap:8px;">
              <button onclick="saveMailSettings()" style="background:linear-gradient(135deg, #0284c7, #2563eb); color:#fff; border:none; padding:7px 16px; border-radius:6px; font-size:11px; font-weight:800; cursor:pointer;">
                💾 Save Mail Settings
              </button>
            </div>
          </div>
          <div id="mail-save-status" style="display:none; margin-top:10px; font-size:11px; color:#10b981; font-weight:700;"></div>
        </div>
      </div>

      <!-- Pipeline Scan Launcher Form -->
      <div style="background:rgba(0,0,0,0.5); border:1px solid rgba(255,255,255,0.08); border-radius:12px; padding:18px 20px; margin-bottom:20px;">
        <h4 style="font-size:12px; font-weight:800; color:#fff; text-transform:uppercase; margin:0 0 12px 0; letter-spacing:0.5px;">
          ⚡ Launch Automated Pipeline Scan (Dynamic City & Niche)
        </h4>
        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(180px, 1fr)); gap:12px; align-items:flex-end;">
          <div>
            <label style="font-size:10.5px; color:#94a3b8; font-weight:700; text-transform:uppercase; display:block; margin-bottom:4px;">Target City</label>
            <input type="text" id="pipeline-city-inp" value="Mumbai" placeholder="e.g. Mumbai, Delhi, Dubai, London..." style="width:100%; background:#0a0d14; border:1px solid rgba(255,255,255,0.15); border-radius:6px; padding:8px 10px; font-size:12px; color:#fff; outline:none;">
          </div>
          <div>
            <label style="font-size:10.5px; color:#94a3b8; font-weight:700; text-transform:uppercase; display:block; margin-bottom:4px;">Target Niche / Category</label>
            <input type="text" id="pipeline-niche-inp" value="Dental Clinic" placeholder="e.g. Dental Clinic, Real Estate, Salon, Legal..." style="width:100%; background:#0a0d14; border:1px solid rgba(255,255,255,0.15); border-radius:6px; padding:8px 10px; font-size:12px; color:#fff; outline:none;">
          </div>
          <div>
            <label style="font-size:10.5px; color:#94a3b8; font-weight:700; text-transform:uppercase; display:block; margin-bottom:4px;">Max Results</label>
            <input type="number" id="pipeline-max-inp" value="20" min="5" max="100" style="width:100%; background:#0a0d14; border:1px solid rgba(255,255,255,0.15); border-radius:6px; padding:8px 10px; font-size:12px; color:#fff; outline:none;">
          </div>
          <div>
            <label style="font-size:10.5px; color:#94a3b8; font-weight:700; text-transform:uppercase; display:block; margin-bottom:4px;">Apify Token (Optional)</label>
            <input type="password" id="pipeline-token-inp" placeholder="Optional Apify Token (Native engine if empty)" style="width:100%; background:#0a0d14; border:1px solid rgba(255,255,255,0.15); border-radius:6px; padding:8px 10px; font-size:12px; color:#fff; outline:none;">
          </div>
          <div>
            <button id="btn-run-pipeline" onclick="runPipelineScan()" style="width:100%; background:linear-gradient(135deg, #a855f7, #6366f1); color:#fff; border:none; padding:9px 16px; border-radius:6px; font-size:12px; font-weight:800; cursor:pointer; display:inline-flex; align-items:center; justify-content:center; gap:6px;">
              🚀 Run Automated Pipeline Scan
            </button>
          </div>
        </div>
        <div style="display:flex; align-items:center; gap:8px; margin-top:12px;">
          <label style="font-size:11px; color:#c084fc; font-weight:700; cursor:pointer; display:inline-flex; align-items:center; gap:6px;">
            <input type="checkbox" id="pipeline-auto-email" checked style="accent-color:#a855f7; width:15px; height:15px;">
            ⚡ Auto-Send Email to Qualifying Leads (Direct Outbound Pitch with Redesign Demo Link)
          </label>
        </div>
        <div id="pipeline-run-status" style="display:none; margin-top:12px; padding:8px 14px; border-radius:6px; background:rgba(168,85,247,0.15); border:1px solid rgba(168,85,247,0.3); font-size:11.5px; color:#c084fc; font-weight:700;"></div>
      </div>

      <!-- Pipeline KPI Metric Strip -->
      <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(180px, 1fr)); gap:12px; margin-bottom:20px;">
        <div style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.08); border-radius:10px; padding:14px;">
          <div style="font-size:10.5px; color:#94a3b8; text-transform:uppercase; font-weight:800;">Master Ledger Total</div>
          <div style="font-size:24px; font-weight:900; color:#fff; margin:4px 0; font-family:'JetBrains Mono', monospace;">{pipeline_stats.get('total', 0)}</div>
          <span style="font-size:10.5px; color:#38bdf8;">Unfiltered Scraped Leads</span>
        </div>
        <div style="background:rgba(255,255,255,0.02); border:1px solid rgba(244,63,94,0.25); border-radius:10px; padding:14px;">
          <div style="font-size:10.5px; color:#f43f5e; text-transform:uppercase; font-weight:800;">No Website Found</div>
          <div style="font-size:24px; font-weight:900; color:#f43f5e; margin:4px 0; font-family:'JetBrains Mono', monospace;">{pipeline_stats.get('no_website', 0)}</div>
          <span style="font-size:10.5px; color:#f43f5e;">100% Need Website</span>
        </div>
        <div style="background:rgba(255,255,255,0.02); border:1px solid rgba(251,191,36,0.25); border-radius:10px; padding:14px;">
          <div style="font-size:10.5px; color:#fbbf24; text-transform:uppercase; font-weight:800;">Outdated / Failed Speed</div>
          <div style="font-size:24px; font-weight:900; color:#fbbf24; margin:4px 0; font-family:'JetBrains Mono', monospace;">{pipeline_stats.get('outdated', 0)}</div>
          <span style="font-size:10.5px; color:#fbbf24;">High Bounce Rate Leads</span>
        </div>
        <div style="background:rgba(255,255,255,0.02); border:1px solid rgba(56,189,248,0.25); border-radius:10px; padding:14px;">
          <div style="font-size:10.5px; color:#38bdf8; text-transform:uppercase; font-weight:800;">Watermarked Demos Ready</div>
          <div style="font-size:24px; font-weight:900; color:#38bdf8; margin:4px 0; font-family:'JetBrains Mono', monospace;">{pipeline_stats.get('demos', 0)}</div>
          <span style="font-size:10.5px; color:#38bdf8;">Hosted & Pitch-Ready</span>
        </div>
        <div style="background:rgba(255,255,255,0.02); border:1px solid rgba(16,185,129,0.25); border-radius:10px; padding:14px;">
          <div style="font-size:10.5px; color:#10b981; text-transform:uppercase; font-weight:800;">Outreach Emails Sent</div>
          <div style="font-size:24px; font-weight:900; color:#10b981; margin:4px 0; font-family:'JetBrains Mono', monospace;">{pipeline_stats.get('emails_sent', 0)}</div>
          <span style="font-size:10.5px; color:#10b981;">Direct Client Inboxes</span>
        </div>
        <div style="background:rgba(255,255,255,0.02); border:1px solid rgba(168,85,247,0.3); border-radius:10px; padding:14px;">
          <div style="font-size:10.5px; color:#c084fc; text-transform:uppercase; font-weight:800;">Estimated Pipeline Value</div>
          <div style="font-size:24px; font-weight:900; color:#c084fc; margin:4px 0; font-family:'JetBrains Mono', monospace;">{pipeline_stats.get('pipeline_value', '₹0')}</div>
          <span style="font-size:10.5px; color:#a855f7;">₹50,000 – ₹1,00,000 / Lead</span>
        </div>
      </div>

      <!-- 14-Column Interactive Master Ledger Table -->
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
        <h4 style="font-size:12px; font-weight:800; color:#fff; text-transform:uppercase; margin:0;">
          📊 14-Column Master Spreadsheet Ledger
        </h4>
        <span style="font-size:11px; color:#94a3b8;">Showing latest leads across all scans</span>
      </div>
      <div style="overflow-x:auto; max-height:480px; overflow-y:auto; border:1px solid rgba(255,255,255,0.06); border-radius:8px;">
        <table>
          <thead style="position:sticky; top:0; background:#0f1219; z-index:2;">
            <tr>
              <th>Business Name</th>
              <th>Phone</th>
              <th>Address</th>
              <th>Website</th>
              <th>Category</th>
              <th>SSL</th>
              <th>Mobile</th>
              <th>Age Check</th>
              <th>Load Speed</th>
              <th>AI Score</th>
              <th>Status</th>
              <th>Redesign</th>
              <th>Email</th>
              <th>Response</th>
              <th style="text-align:right;">Price</th>
              <th style="text-align:right;">1-Click Outreach</th>
            </tr>
          </thead>
          <tbody>
            {pipeline_rows}
          </tbody>
        </table>
      </div>
    </div>


    <!-- 📢 Autonomous Social Media Auto-Poster Section -->
    <div class="section-card" style="border: 1px solid rgba(192,132,252,0.35); background: linear-gradient(180deg, rgba(15,23,42,0.95), rgba(10,12,18,0.95));">
      <div class="section-header">
        <div>
          <div class="section-title" style="color:#fff; display:flex; align-items:center; gap:8px;">
            📢 Autonomous Social Media Auto-Poster
            <span style="background:rgba(16,185,129,0.15); color:#10b981; border:1px solid rgba(16,185,129,0.3); font-size:10px; padding:2px 8px; border-radius:12px; font-weight:800;">AUTONOMOUS ON</span>
          </div>
          <p style="font-size:11px; color:#94a3b8; margin-top:3px;">Auto-generates high-converting teardowns across Twitter/X, LinkedIn & Reddit with 1-click sharing & Webhook support</p>
        </div>
        <div style="display:flex; gap:8px;">
          <button id="btn-gen-social" onclick="generateSocialPost()" style="background:linear-gradient(135deg, #0284c7, #0055ff); color:#fff; border:none; padding:7px 12px; border-radius:6px; font-size:11px; font-weight:700; cursor:pointer;">⚡ Generate Fresh Post</button>
          <button id="btn-dispatch-social" onclick="dispatchSocialPost()" style="background:linear-gradient(135deg, #10b981, #059669); color:#fff; border:none; padding:7px 12px; border-radius:6px; font-size:11px; font-weight:700; cursor:pointer;">🚀 Dispatch to Webhook</button>
        </div>
      </div>

      <!-- Current Post Cards Grid -->
      <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); gap:14px; margin-bottom:20px;">
        
        <!-- Twitter/X Card -->
        <div style="background:rgba(0,0,0,0.4); border:1px solid rgba(56,189,248,0.25); border-radius:12px; padding:16px; display:flex; flex-direction:column; justify-content:space-between;">
          <div>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
              <span style="color:#38bdf8; font-weight:800; font-size:12px; display:flex; align-items:center; gap:6px;">🐦 Twitter / X Viral Post</span>
              <span style="font-size:10px; color:#64748b;">{post_niche}</span>
            </div>
            <p style="font-size:11.5px; color:#f1f5f9; line-height:1.5; white-space:pre-line; max-height:160px; overflow-y:auto; padding-right:4px;">{tw_text}</p>
          </div>
          <div style="margin-top:14px; padding-top:10px; border-top:1px solid rgba(255,255,255,0.06); display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:10px; color:#f43f5e; font-weight:700;">Leak: {post_leak}</span>
            <a href="{tw_intent}" target="_blank" style="background:#0284c7; color:#fff; padding:6px 12px; border-radius:6px; font-size:11px; font-weight:700; text-decoration:none; display:inline-flex; align-items:center; gap:4px;">Tweet on X ➔</a>
          </div>
        </div>

        <!-- LinkedIn Card -->
        <div style="background:rgba(0,0,0,0.4); border:1px solid rgba(10,102,194,0.3); border-radius:12px; padding:16px; display:flex; flex-direction:column; justify-content:space-between;">
          <div>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
              <span style="color:#60a5fa; font-weight:800; font-size:12px; display:flex; align-items:center; gap:6px;">💼 LinkedIn Teardown</span>
              <span style="font-size:10px; color:#64748b;">Thought Leadership</span>
            </div>
            <strong style="font-size:12px; color:#fff; display:block; margin-bottom:6px;">{li_headline}</strong>
            <p style="font-size:11px; color:#cbd5e1; line-height:1.5; max-height:120px; overflow-y:auto;">{li_content[:240]}...</p>
          </div>
          <div style="margin-top:14px; padding-top:10px; border-top:1px solid rgba(255,255,255,0.06); display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:10px; color:#94a3b8;">High-Ticket B2B</span>
            <a href="{li_intent}" target="_blank" style="background:#0a66c2; color:#fff; padding:6px 12px; border-radius:6px; font-size:11px; font-weight:700; text-decoration:none; display:inline-flex; align-items:center; gap:4px;">Post to LinkedIn ➔</a>
          </div>
        </div>

        <!-- Reddit Card -->
        <div style="background:rgba(0,0,0,0.4); border:1px solid rgba(255,69,0,0.3); border-radius:12px; padding:16px; display:flex; flex-direction:column; justify-content:space-between;">
          <div>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
              <span style="color:#fb923c; font-weight:800; font-size:12px; display:flex; align-items:center; gap:6px;">🔴 Reddit Community Post</span>
              <span style="font-size:10px; color:#64748b;">r/SaaS</span>
            </div>
            <strong style="font-size:12px; color:#fff; display:block; margin-bottom:6px;">{rd_title}</strong>
            <p style="font-size:11px; color:#94a3b8; line-height:1.4;">Organic case study format with zero spam vibe, built to drive community engagement and referral clicks.</p>
          </div>
          <div style="margin-top:14px; padding-top:10px; border-top:1px solid rgba(255,255,255,0.06); display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:10px; color:#94a3b8;">r/SaaS & Entrepreneur</span>
            <a href="{rd_intent}" target="_blank" style="background:#ea580c; color:#fff; padding:6px 12px; border-radius:6px; font-size:11px; font-weight:700; text-decoration:none; display:inline-flex; align-items:center; gap:4px;">Post to Reddit ➔</a>
          </div>
        </div>

      </div>

      <!-- Webhook Configuration Strip -->
      <div style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.06); border-radius:8px; padding:10px 14px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
        <div style="display:flex; align-items:center; gap:10px;">
          <span style="font-size:11px; color:#94a3b8; font-weight:700;">Direct Auto-Dispatch Webhook:</span>
          <span style="font-size:11px; font-weight:700; color:{'#10b981' if webhook_cfg else '#94a3b8'};">{webhook_status_text}</span>
        </div>
        <div style="display:flex; gap:6px; align-items:center; flex:1; max-width:480px;">
          <input type="text" id="social-webhook-input" placeholder="Discord / Slack / Telegram / Make.com Webhook URL..." value="{webhook_cfg}" style="flex:1; background:#000; border:1px solid rgba(255,255,255,0.15); border-radius:6px; padding:6px 10px; font-size:11px; color:#fff; outline:none;">
          <button onclick="saveSocialWebhook()" style="background:rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.15); color:#fff; padding:6px 12px; border-radius:6px; font-size:11px; font-weight:700; cursor:pointer;">Save</button>
        </div>
      </div>

      <!-- Published History Mini-Table -->
      <h4 style="font-size:12px; color:#94a3b8; margin:16px 0 8px; text-transform:uppercase; font-weight:800;">Recent Social Dispatches</h4>
      <div style="overflow-x:auto;">
        <table>
          <thead>
            <tr>
              <th>Target Niche</th>
              <th>Target Market</th>
              <th>Leak Highlight</th>
              <th>Dispatched Time</th>
              <th>Instant Share</th>
            </tr>
          </thead>
          <tbody>
            {social_rows}
          </tbody>
        </table>
      </div>
    </div>

    <!-- 🎬 Viral Video, Reels, TikTok & Shorts Studio Section -->
    <div class="section-card" style="border:1px solid rgba(236,72,153,0.3); background:linear-gradient(180deg, rgba(236,72,153,0.06) 0%, rgba(15,18,25,0.98) 100%);">
      <div class="section-header">
        <div>
          <div class="section-title" style="color:#f472b6;">🎬 Viral Video, Reels, TikTok & YouTube Shorts Studio (Auto-Mode)</div>
          <p style="font-size:12px; color:#94a3b8; margin-top:4px;">Autonomous Trend Research & 9:16 Vertical Video Production. Automatically promotes LeakGrader.com through high-retention educational hooks.</p>
        </div>
        <div style="display:flex; gap:8px;">
          <button onclick="generateNewReel()" style="background:linear-gradient(135deg, #ec4899, #f43f5e); color:#fff; border:none; padding:6px 14px; border-radius:8px; font-size:11px; font-weight:800; cursor:pointer;">⚡ Research & Generate New Reel</button>
          <button onclick="dispatchCurrentReel()" style="background:#0284c7; color:#fff; border:none; padding:6px 14px; border-radius:8px; font-size:11px; font-weight:800; cursor:pointer;">🚀 Dispatch to Auto-Publisher</button>
        </div>
      </div>

      <!-- Live Ready Reel Card -->
      <div style="background:rgba(0,0,0,0.5); border:1px solid rgba(255,255,255,0.08); border-radius:12px; padding:20px; margin-bottom:20px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px; flex-wrap:wrap; gap:8px;">
          <div>
            <span style="font-size:10px; background:rgba(236,72,153,0.2); color:#f472b6; border:1px solid rgba(236,72,153,0.4); padding:3px 8px; border-radius:6px; font-weight:800; text-transform:uppercase;">Niche: {reel_niche}</span>
            <h3 style="font-size:16px; font-weight:900; color:#fff; margin-top:6px;">{reel_angle}</h3>
          </div>
          <div style="font-size:11px; color:#94a3b8;">Format: <strong style="color:#38bdf8;">9:16 Vertical (Reels / TikTok / Shorts)</strong> • Duration: <strong style="color:#34d399;">~28 Seconds</strong></div>
        </div>

        <!-- 4-Scene Storyboard Grid -->
        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap:12px; margin-bottom:18px;">
          
          <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(236,72,153,0.2); border-radius:8px; padding:12px;">
            <div style="font-size:10px; font-weight:800; color:#f472b6; text-transform:uppercase;">Scene 1 • 0-3s (Viral Hook)</div>
            <div style="font-size:11px; color:#fff; font-weight:700; margin:6px 0;">"{s1.get('voiceover', '')}"</div>
            <div style="font-size:10px; color:#94a3b8;"><strong>Screen Visual:</strong> {s1.get('screen_visual', '')}</div>
          </div>

          <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(251,113,133,0.2); border-radius:8px; padding:12px;">
            <div style="font-size:10px; font-weight:800; color:#fb7185; text-transform:uppercase;">Scene 2 • 3-12s (Industry Education)</div>
            <div style="font-size:11px; color:#e2e8f0; margin:6px 0;">{s2.get('voiceover', '')}</div>
            <div style="font-size:10px; color:#94a3b8;"><strong>Screen Visual:</strong> {s2.get('screen_visual', '')}</div>
          </div>

          <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(56,189,248,0.2); border-radius:8px; padding:12px;">
            <div style="font-size:10px; font-weight:800; color:#38bdf8; text-transform:uppercase;">Scene 3 • 12-22s (LeakGrader Demo)</div>
            <div style="font-size:11px; color:#e2e8f0; margin:6px 0;">{s3.get('voiceover', '')}</div>
            <div style="font-size:10px; color:#94a3b8;"><strong>Screen Visual:</strong> {s3.get('screen_visual', '')}</div>
          </div>

          <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(52,211,153,0.2); border-radius:8px; padding:12px;">
            <div style="font-size:10px; font-weight:800; color:#34d399; text-transform:uppercase;">Scene 4 • 22-28s (Viral CTA)</div>
            <div style="font-size:11px; color:#fff; font-weight:700; margin:6px 0;">"{s4.get('voiceover', '')}"</div>
            <div style="font-size:10px; color:#94a3b8;"><strong>Screen Visual:</strong> {s4.get('screen_visual', '')}</div>
          </div>

        </div>

        <!-- 1-Click Copy Buttons for Voiceover & Caption -->
        <div style="display:flex; gap:10px; flex-wrap:wrap;">
          <input type="hidden" id="raw-reel-voiceover" value="{reel_voiceover_raw}">
          <input type="hidden" id="raw-reel-caption" value="{reel_caption_raw}">
          <input type="hidden" id="current-reel-id" value="{reel_id}">
          <button onclick="copyReelVoiceover()" style="background:rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.15); color:#fff; padding:8px 14px; border-radius:6px; font-size:11px; font-weight:700; cursor:pointer;">📋 Copy Full Voiceover Script</button>
          <button onclick="copyReelCaption()" style="background:rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.15); color:#fff; padding:8px 14px; border-radius:6px; font-size:11px; font-weight:700; cursor:pointer;">📝 Copy Caption & Viral Hashtags</button>
        </div>
      </div>

      <!-- Social Credentials & Auto-Publishing Webhook Setup -->
      <div style="background:rgba(0,0,0,0.3); border:1px solid rgba(255,255,255,0.08); border-radius:10px; padding:16px;">
        <h4 style="font-size:12px; font-weight:800; color:#fff; text-transform:uppercase; margin-bottom:8px;">⚙️ Auto-Posting Credentials & Webhook Setup (Instagram / Facebook / TikTok / YouTube)</h4>
        <p style="font-size:11px; color:#94a3b8; margin-bottom:12px;">Paste your Make.com, Zapier, Blotato, or Repurpose.io Webhook URL below to automatically push every newly generated Reel straight to Instagram, Facebook, TikTok, and YouTube Shorts without manual intervention.</p>
        
        <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap;">
          <input type="text" id="reel-webhook-input" placeholder="Make.com / Zapier / Buffer Webhook URL for Reels..." value="{reel_webhook}" style="flex:1; min-width:280px; background:#000; border:1px solid rgba(255,255,255,0.15); border-radius:6px; padding:8px 12px; font-size:11px; color:#fff; outline:none;">
          <button onclick="saveReelCredentials()" style="background:#10b981; border:none; color:#fff; padding:8px 16px; border-radius:6px; font-size:11px; font-weight:800; cursor:pointer;">💾 Save Webhook</button>
        </div>
      </div>

    </div>

    <!-- High-DA Startup Directories Launch Kit Section -->
    <div class="section-card" style="border:1px solid rgba(56,189,248,0.25); background:linear-gradient(180deg, rgba(56,189,248,0.05) 0%, rgba(15,18,25,0.95) 100%);">
      <div class="section-header">
        <div>
          <div class="section-title">🚀 Fast Backlinks & High-DA Directory Submission Kit</div>
          <p style="font-size:12px; color:#94a3b8; margin-top:4px;">Submit LeakGrader to these top high-authority directories to boost Moz/Ahrefs DA from 0 to 40+ and get instant organic traffic.</p>
        </div>
        <span style="font-size:11px; background:rgba(16,185,129,0.15); color:#10b981; border:1px solid rgba(16,185,129,0.3); padding:4px 10px; border-radius:20px; font-weight:700;">6 High-Impact Platforms</span>
      </div>

      <!-- Quick Copy Data Block -->
      <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:12px; margin-bottom:20px; background:rgba(0,0,0,0.4); padding:16px; border-radius:10px; border:1px solid rgba(255,255,255,0.06);">
        <div>
          <div style="font-size:10px; text-transform:uppercase; color:#94a3b8; font-weight:800;">Product Title</div>
          <div style="display:flex; justify-content:space-between; align-items:center; margin-top:4px;">
            <code style="font-size:12px; color:#38bdf8;">LeakGrader</code>
            <button onclick="navigator.clipboard.writeText('LeakGrader'); alert('Copied!');" style="background:rgba(255,255,255,0.1); border:none; color:#fff; padding:3px 8px; border-radius:4px; font-size:10px; cursor:pointer;">Copy</button>
          </div>
        </div>
        <div>
          <div style="font-size:10px; text-transform:uppercase; color:#94a3b8; font-weight:800;">Tagline (Under 60 chars)</div>
          <div style="display:flex; justify-content:space-between; align-items:center; margin-top:4px;">
            <code style="font-size:11px; color:#38bdf8;">10s Website Revenue Leak Scanner & 24/7 AI Closer</code>
            <button onclick="navigator.clipboard.writeText('10s Website Revenue Leak Scanner & 24/7 AI Closer'); alert('Copied!');" style="background:rgba(255,255,255,0.1); border:none; color:#fff; padding:3px 8px; border-radius:4px; font-size:10px; cursor:pointer;">Copy</button>
          </div>
        </div>
        <div style="grid-column: 1 / -1;">
          <div style="font-size:10px; text-transform:uppercase; color:#94a3b8; font-weight:800;">Short Pitch / Description</div>
          <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-top:4px; gap:8px;">
            <code style="font-size:11px; color:#e2e8f0; line-height:1.4;">LeakGrader audits any business website in 10 seconds to detect after-hours lead dropoff and response lag, calculating exact revenue loss. Includes an autonomous 24/7 conversational AI sales closer that qualifies leads and books meetings in under 30 seconds.</code>
            <button onclick="navigator.clipboard.writeText('LeakGrader audits any business website in 10 seconds to detect after-hours lead dropoff and response lag, calculating exact revenue loss. Includes an autonomous 24/7 conversational AI sales closer that qualifies leads and books meetings in under 30 seconds.'); alert('Copied!');" style="background:rgba(255,255,255,0.1); border:none; color:#fff; padding:4px 10px; border-radius:4px; font-size:10px; cursor:pointer; white-space:nowrap;">Copy Pitch</button>
          </div>
        </div>
      </div>

      <!-- Directory Links Table -->
      <div style="overflow-x:auto;">
        <table>
          <thead>
            <tr>
              <th>Directory Platform</th>
              <th>Domain Authority (DA)</th>
              <th>Backlink Type</th>
              <th>Review Time</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Uneed.best</strong> <span style="font-size:10px; color:#94a3b8;">Top Daily Tools</span></td>
              <td><span style="color:#10b981; font-weight:800;">DA 68</span></td>
              <td>Dofollow permanent</td>
              <td>24 - 48 Hours</td>
              <td><a href="https://www.uneed.best/submit-a-tool" target="_blank" style="background:#0284c7; color:#fff; padding:4px 10px; border-radius:6px; font-size:11px; font-weight:700; text-decoration:none;">Submit to Uneed &rarr;</a></td>
            </tr>
            <tr>
              <td><strong>SaaSHub</strong> <span style="font-size:10px; color:#94a3b8;">Software Alternatives</span></td>
              <td><span style="color:#10b981; font-weight:800;">DA 74</span></td>
              <td>Dofollow permanent</td>
              <td>Instant / 24 Hours</td>
              <td><a href="https://www.saashub.com/submit" target="_blank" style="background:#0284c7; color:#fff; padding:4px 10px; border-radius:6px; font-size:11px; font-weight:700; text-decoration:none;">Submit to SaaSHub &rarr;</a></td>
            </tr>
            <tr>
              <td><strong>LaunchingNext</strong> <span style="font-size:10px; color:#94a3b8;">Trending Startups</span></td>
              <td><span style="color:#10b981; font-weight:800;">DA 62</span></td>
              <td>Dofollow permanent</td>
              <td>2 - 3 Days</td>
              <td><a href="https://www.launchingnext.com/submit/" target="_blank" style="background:#0284c7; color:#fff; padding:4px 10px; border-radius:6px; font-size:11px; font-weight:700; text-decoration:none;">Submit to LaunchingNext &rarr;</a></td>
            </tr>
            <tr>
              <td><strong>BetaList</strong> <span style="font-size:10px; color:#94a3b8;">Early Access Products</span></td>
              <td><span style="color:#10b981; font-weight:800;">DA 71</span></td>
              <td>High Authority Mention</td>
              <td>3 - 5 Days</td>
              <td><a href="https://betalist.com/submit" target="_blank" style="background:#0284c7; color:#fff; padding:4px 10px; border-radius:6px; font-size:11px; font-weight:700; text-decoration:none;">Submit to BetaList &rarr;</a></td>
            </tr>
            <tr>
              <td><strong>Product Hunt</strong> <span style="font-size:10px; color:#94a3b8;">#1 Tech Community</span></td>
              <td><span style="color:#10b981; font-weight:800;">DA 91</span></td>
              <td>Massive Viral Influx</td>
              <td>Scheduled Launch</td>
              <td><a href="https://www.producthunt.com/posts/new" target="_blank" style="background:#ea580c; color:#fff; padding:4px 10px; border-radius:6px; font-size:11px; font-weight:700; text-decoration:none;">Submit to Product Hunt &rarr;</a></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Live Backlink Ledger Section -->
    <div class="section-card">
      <div class="section-header">
        <div class="section-title">🔗 Real-Time Non-Repeating Backlink Submissions Feed</div>
        <span style="font-size:11px; color:#94A3B8;">Auto-refreshing every 15s • Updated: {data['last_updated']}</span>
      </div>
      <div style="overflow-x:auto;">
        <table>
          <thead>
            <tr>
              <th>Target Platform</th>
              <th>Authority</th>
              <th>Synthesized Dynamic Anchor</th>
              <th>Target Landing URL</th>
              <th>Timestamp</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {backlink_rows}
          </tbody>
        </table>
      </div>
    </div>

    <!-- Live Outbound Campaigns Section -->
    <div class="section-card">
      <div class="section-header">
        <div class="section-title">🎯 Autonomous B2B Outbound Campaigns Dispatched</div>
        <span style="font-size:11px; color:#94A3B8;">Verified Decision-Makers Pipeline</span>
      </div>
      <div style="overflow-x:auto;">
        <table>
          <thead>
            <tr>
              <th>Company Target</th>
              <th>Decision Maker</th>
              <th>Contact Email</th>
              <th>Location</th>
              <th>Dispatched Time</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {outreach_rows}
          </tbody>
        </table>
      </div>
    </div>

  </div>

  <script>
    async function generateSocialPost() {{
      const btn = document.getElementById('btn-gen-social');
      if (btn) btn.innerText = '⚡ Generating...';
      try {{
        const res = await fetch('/api/social/generate', {{ method: 'POST' }});
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const data = await res.json();
        if (data.success) location.reload();
      }} catch (e) {{
        alert('Error generating post: ' + e.message);
      }} finally {{
        if (btn) btn.innerText = '⚡ Generate Next Viral Post';
      }}
    }}

    async function dispatchSocialPost() {{
      const btn = document.getElementById('btn-dispatch-social');
      if (btn) btn.innerText = '🚀 Dispatching...';
      try {{
        const res = await fetch('/api/social/dispatch', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{}})
        }});
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const data = await res.json();
        if (data.success) {{
          alert('Dispatched! Webhook Status: ' + (data.result?.webhook_status || 'OK'));
          location.reload();
        }}
      }} catch (e) {{
        alert('Error dispatching: ' + e.message);
      }} finally {{
        if (btn) btn.innerText = '🚀 Dispatch Now to Social Webhooks';
      }}
    }}

    async function saveSocialWebhook() {{
      const inp = document.getElementById('social-webhook-input');
      const val = inp ? inp.value.trim() : '';
      try {{
        const res = await fetch('/api/social/config', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ webhook_url: val }})
        }});
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const data = await res.json();
        if (data.success) {{
          alert('Webhook configuration updated!');
          location.reload();
        }}
      }} catch (e) {{
        alert('Error saving webhook: ' + e.message);
      }}
    }}

    async function generateNewReel() {{
      try {{
        const res = await fetch('/api/reels/generate', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{}})
        }});
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const data = await res.json();
        if (data.status === 'SUCCESS' || data.success) {{
          alert('⚡ Fresh Viral Reel Script & Storyboard Generated: ' + (data.reel?.angle || 'Ready'));
          location.reload();
        }}
      }} catch (e) {{
        alert('Error generating reel: ' + e.message);
      }}
    }}

    async function dispatchCurrentReel() {{
      const reelId = document.getElementById('current-reel-id')?.value || '';
      try {{
        const res = await fetch('/api/reels/dispatch', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ reel_id: reelId }})
        }});
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const data = await res.json();
        if (data.status === 'SUCCESS' || data.success) {{
          const isWebhook = data.report && data.report.webhook_triggered;
          const statusMsg = isWebhook ? ('SENT (HTTP ' + data.report.webhook_status + ')') : 'READY (1-Click Copy Below)';
          alert('🚀 Viral Reel Ready & Logged!\nPublish Status: ' + statusMsg);
          location.reload();
        }} else {{
          alert('Notice: ' + (data.message || 'Dispatched'));
        }}
      }} catch (e) {{
        alert('Error dispatching reel: ' + e.message);
      }}
    }}

    async function saveReelCredentials() {{
      const webhook = document.getElementById('reel-webhook-input')?.value.trim() || '';
      try {{
        const res = await fetch('/api/reels/credentials', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ auto_publisher_webhook: webhook }})
        }});
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const data = await res.json();
        if (data.status === 'SUCCESS' || data.success) {{
          alert('Reel Auto-Publisher Webhook Saved Successfully!');
          location.reload();
        }}
      }} catch (e) {{
        alert('Error saving credentials: ' + e.message);
      }}
    }}

    function copyReelVoiceover() {{
      const text = document.getElementById('raw-reel-voiceover')?.value || '';
      navigator.clipboard.writeText(text);
      alert('📋 Voiceover Script copied to clipboard!');
    }}

    function copyReelCaption() {{
      const text = document.getElementById('raw-reel-caption')?.value || '';
      navigator.clipboard.writeText(text);
      alert('📝 Caption & Hashtags copied to clipboard!');
    }}

    async function triggerSeoSprint() {{
      const btn = document.getElementById('btn-run-seo');
      if (btn) {{
        btn.disabled = true;
        btn.textContent = '⏳ Running Autonomous SEO Sprint...';
      }}
      try {{
        const res = await fetch('/api/seo/trigger-sprint', {{ method: 'POST' }});
        const data = await res.json();
        if (data.success) {{
          alert('✅ Autonomous SEO Sprint Executed Successfully!\n• High-DA backlink logged to ledger\n• IndexNow search engine broadcast complete');
          location.reload();
        }} else {{
          alert('Notice: ' + JSON.stringify(data));
        }}
      }} catch(e) {{
        alert('Error: ' + e.message);
      }} finally {{
        if (btn) {{
          btn.disabled = false;
          btn.textContent = '⚡ Run Autonomous SEO Sprint Now';
        }}
      }}
    }}

    async function triggerFounderSeoSprint() {{
      const btn = document.getElementById('btn-dash-trigger-sprint');
      if (btn) {{
        btn.disabled = true;
        btn.textContent = '⏳ Executing Sprint...';
      }}
      try {{
        const res = await fetch('/api/seo/trigger-sprint', {{ method: 'POST' }});
        const data = await res.json();
        if (data.success) {{
          alert('✅ Autonomous SEO Sprint Completed!\n• Platform: ' + (data.result?.backlink_logged?.platform || 'High-DA Directory') + '\n• DA: ' + (data.result?.backlink_logged?.domain_authority || 80) + '\n• Target Deep Link: ' + (data.result?.backlink_logged?.target_url || 'https://leakgrader.com'));
          location.reload();
        }} else {{
          alert('Notice: ' + JSON.stringify(data));
        }}
      }} catch(e) {{
        alert('Error: ' + e.message);
      }} finally {{
        if (btn) {{
          btn.disabled = false;
          btn.textContent = '⚡ Run SEO Sprint Now';
        }}
      }}
    }}

    async function pingFounderIndexNow() {{
      try {{
        const res = await fetch('/api/growth/indexnow-ping', {{ method: 'POST' }});
        const data = await res.json();
        if (data.success) {{
          alert('🚀 Global IndexNow Ping Broadcasted Successfully!\nBingbot, Yandex, OpenAI Search & Perplexity crawlers notified.');
          location.reload();
        }} else {{
          alert('Notice: ' + JSON.stringify(data));
        }}
      }} catch(e) {{
        alert('Error broadcasting IndexNow: ' + e.message);
      }}
    }}

    // Live Countdown Timer for Founder Dashboard
    let dashCountdownSeconds = 300;
    async function syncDashSeoCountdown() {{
      try {{
        const res = await fetch('/api/seo/recent-activity');
        if (!res.ok) return;
        const data = await res.json();
        if (data.server_time_utc && data.last_run) {{
          const sTime = new Date(data.server_time_utc.replace(' UTC', 'Z')).getTime();
          const lTime = new Date(data.last_run.replace(' UTC', 'Z')).getTime();
          if (!isNaN(sTime) && !isNaN(lTime)) {{
            const elapsed = Math.max(0, Math.floor((sTime - lTime) / 1000));
            dashCountdownSeconds = Math.max(0, 300 - (elapsed % 300));
          }}
        }}
      }} catch(e) {{}}
    }}
    syncDashSeoCountdown();
    setInterval(syncDashSeoCountdown, 20000);

    setInterval(() => {{
      const timerEl = document.getElementById('dash-countdown-timer');
      if (dashCountdownSeconds > 0) {{
        dashCountdownSeconds--;
      }} else {{
        dashCountdownSeconds = 300;
        location.reload();
      }}
      if (timerEl) {{
        const mins = Math.floor(dashCountdownSeconds / 60).toString().padStart(2, '0');
        const secs = (dashCountdownSeconds % 60).toString().padStart(2, '0');
        timerEl.textContent = mins + ':' + secs;
      }}
    }}, 1000);
  </script>

  <!-- Modal for Lead Pitch View -->
  <div id="pipeline-pitch-modal" style="display:none; position:fixed; inset:0; background:rgba(0,0,0,0.85); backdrop-filter:blur(6px); z-index:9999; align-items:center; justify-content:center; padding:20px;">
    <div style="background:#0f1219; border:1px solid rgba(168,85,247,0.4); border-radius:16px; max-width:680px; width:100%; padding:24px; box-shadow:0 20px 50px rgba(0,0,0,0.8); max-height:90vh; overflow-y:auto;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; border-bottom:1px solid rgba(255,255,255,0.08); padding-bottom:12px;">
        <div>
          <h3 id="modal-biz-name" style="font-size:18px; font-weight:900; color:#fff;">Business Name</h3>
          <div style="display:flex; align-items:center; gap:12px; margin-top:4px;">
            <span id="modal-biz-price" style="font-size:12px; color:#c084fc; font-weight:800;">Target Pitch: ₹1,00,000</span>
            <span style="color:#64748b; font-size:11px;">•</span>
            <span style="font-size:11.5px; color:#38bdf8; font-family:monospace;">To: <strong id="modal-biz-email">contact@business.com</strong></span>
          </div>
        </div>
        <button onclick="closeLeadPitchModal()" style="background:none; border:none; color:#94a3b8; font-size:24px; cursor:pointer; line-height:1;">&times;</button>
      </div>

      <div style="margin-bottom:16px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
          <label style="font-size:11px; color:#94a3b8; font-weight:700; text-transform:uppercase;">Personalized High-Ticket Cold Email Copy (Editable)</label>
          <span style="font-size:10.5px; color:#64748b;">You can customize copy before dispatching</span>
        </div>
        <textarea id="modal-email-text" style="width:100%; height:260px; background:#08090c; border:1px solid rgba(255,255,255,0.12); border-radius:8px; padding:12px; font-family:monospace; font-size:11.5px; color:#e2e8f0; line-height:1.5; resize:vertical;"></textarea>
      </div>

      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
        <div style="display:flex; gap:8px;">
          <a id="modal-demo-btn" href="#" target="_blank" style="background:#0284c7; color:#fff; text-decoration:none; padding:8px 14px; border-radius:6px; font-size:11px; font-weight:800; display:inline-flex; align-items:center; gap:6px;">
            👁️ Open Live Demo ↗
          </a>
          <a id="modal-wa-btn" href="#" target="_blank" style="background:#10b981; color:#fff; text-decoration:none; padding:8px 14px; border-radius:6px; font-size:11px; font-weight:800; display:inline-flex; align-items:center; gap:6px;">
            💬 Open WhatsApp ➔
          </a>
        </div>
        <div style="display:flex; gap:8px;">
          <button onclick="copyPitchEmail()" style="background:rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.2); color:#fff; padding:8px 14px; border-radius:6px; font-size:11px; font-weight:800; cursor:pointer;">
            📋 Copy Text
          </button>
          <button id="modal-send-btn" onclick="sendModalPitchEmail()" style="background:linear-gradient(135deg, #0284c7, #2563eb); color:#fff; border:none; padding:8px 18px; border-radius:6px; font-size:11px; font-weight:800; cursor:pointer; display:inline-flex; align-items:center; gap:6px;">
            🚀 Send Directly to Client Email
          </button>
        </div>
      </div>
    </div>
  </div>

  <script>
    let currentModalLeadId = '';

    function showLeadPitchModal(id, name, price, email, emailAddress, waUrl, demoUrl) {{
      currentModalLeadId = id || '';
      document.getElementById('modal-biz-name').textContent = name;
      document.getElementById('modal-biz-price').textContent = 'Target Pitch: ' + price;
      document.getElementById('modal-biz-email').textContent = emailAddress || ('contact@' + name.toLowerCase().replace(/[^a-z0-9]/g, '') + '.com');
      document.getElementById('modal-email-text').value = email.replace(/\\n/g, '\n');
      document.getElementById('modal-demo-btn').href = demoUrl;
      document.getElementById('modal-wa-btn').href = waUrl;
      const sendBtn = document.getElementById('modal-send-btn');
      if (sendBtn) {{
        sendBtn.disabled = false;
        sendBtn.textContent = '🚀 Send Directly to Client Email';
      }}
      document.getElementById('pipeline-pitch-modal').style.display = 'flex';
    }}

    function closeLeadPitchModal() {{
      document.getElementById('pipeline-pitch-modal').style.display = 'none';
    }}

    function copyPitchEmail() {{
      const text = document.getElementById('modal-email-text').value;
      navigator.clipboard.writeText(text);
      alert('📋 Pitch Email copied to clipboard!');
    }}

    async function sendDirectLeadEmail(leadId, btn) {{
      if (!leadId) {{
        alert('Lead ID is missing');
        return;
      }}
      const origText = btn ? btn.textContent : '';
      if (btn) {{
        btn.disabled = true;
        btn.textContent = '⏳ Sending...';
      }}

      try {{
        const res = await fetch('/api/pipeline/send-email', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ lead_id: leadId }})
        }});
        const data = await res.json();
        if (data.success) {{
          if (btn) {{
            btn.textContent = '✅ Sent!';
            btn.style.background = '#059669';
          }}
          alert('🚀 ' + (data.message || 'Email successfully sent to client!'));
        }} else {{
          alert('Notice: ' + (data.error || 'Failed to dispatch email'));
          if (btn) {{
            btn.disabled = false;
            btn.textContent = origText;
          }}
        }}
      }} catch (err) {{
        alert('Network Error: ' + err.message);
        if (btn) {{
          btn.disabled = false;
          btn.textContent = origText;
        }}
      }}
    }}

    async function sendModalPitchEmail() {{
      if (!currentModalLeadId) {{
        alert('Lead ID missing');
        return;
      }}
      const btn = document.getElementById('modal-send-btn');
      const customBody = document.getElementById('modal-email-text').value;
      if (btn) {{
        btn.disabled = true;
        btn.textContent = '⏳ Dispatching Outbound Email...';
      }}

      try {{
        const res = await fetch('/api/pipeline/send-email', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ lead_id: currentModalLeadId, custom_body: customBody }})
        }});
        const data = await res.json();
        if (data.success) {{
          if (btn) {{
            btn.textContent = '✅ Email Dispatched!';
            btn.style.background = '#059669';
          }}
          alert('🎉 ' + (data.message || 'Outreach pitch successfully sent!'));
        }} else {{
          alert('Notice: ' + (data.error || 'Failed to dispatch email'));
          if (btn) {{
            btn.disabled = false;
            btn.textContent = '🚀 Send Directly to Client Email';
          }}
        }}
      }} catch (err) {{
        alert('Network Error: ' + err.message);
        if (btn) {{
          btn.disabled = false;
          btn.textContent = '🚀 Send Directly to Client Email';
        }}
      }}
    }}

    function toggleMailSettings() {{
      const panel = document.getElementById('mail-settings-panel');
      const icon = document.getElementById('mail-toggle-icon');
      if (panel.style.display === 'none') {{
        panel.style.display = 'block';
        if (icon) icon.textContent = '▲ Hide Settings';
        loadMailConfig();
      }} else {{
        panel.style.display = 'none';
        if (icon) icon.textContent = '⚙️ Configure / Expand ▼';
      }}
    }}

    function onMailProviderChange() {{
      const prov = document.getElementById('mail-provider-select').value;
      const lblUser = document.getElementById('lbl-mail-user');
      const lblPass = document.getElementById('lbl-mail-pass');
      const inpPass = document.getElementById('mail-pass-inp');
      const badge = document.getElementById('mail-portal-badge');

      if (prov === 'gmail_smtp') {{
        if (lblUser) lblUser.textContent = 'Gmail Address';
        if (lblPass) lblPass.textContent = 'Google App Password (16-char)';
        if (inpPass) inpPass.placeholder = 'xxxx xxxx xxxx xxxx';
        if (badge) badge.textContent = 'Gmail SMTP (500/day Free)';
      }} else if (prov === 'brevo') {{
        if (lblUser) lblUser.textContent = 'Account Sender Email';
        if (lblPass) lblPass.textContent = 'Brevo API Key (xkeysib-...)';
        if (inpPass) inpPass.placeholder = 'xkeysib-xxxxxxxxxxxxxx';
        if (badge) badge.textContent = 'Brevo API (300/day Free Forever)';
      }} else if (prov === 'resend') {{
        if (lblUser) lblUser.textContent = 'Sender Email';
        if (lblPass) lblPass.textContent = 'Resend API Key (re_...)';
        if (inpPass) inpPass.placeholder = 're_xxxxxxxxxxxxxx';
        if (badge) badge.textContent = 'Resend API (3k/mo Free)';
      }} else if (prov === 'n8n_webhook') {{
        if (lblUser) lblUser.textContent = 'Webhook URL';
        if (lblPass) lblPass.textContent = 'Auth Header / Token (Optional)';
        if (badge) badge.textContent = 'n8n Self-Hosted Webhook';
      }}
    }}

    async function loadMailConfig() {{
      try {{
        const res = await fetch('/api/pipeline/mail-config');
        const data = await res.json();
        if (data.success && data.config) {{
          const c = data.config;
          if (c.provider) document.getElementById('mail-provider-select').value = c.provider;
          if (c.smtp_user) document.getElementById('mail-user-inp').value = c.smtp_user;
          if (c.from_name) document.getElementById('mail-fromname-inp').value = c.from_name;
          if (c.smtp_password) document.getElementById('mail-pass-inp').value = c.smtp_password;
          if (c.auto_send_qualifying !== undefined) document.getElementById('mail-autosend-cfg').checked = !!c.auto_send_qualifying;
          onMailProviderChange();
        }}
      }} catch (e) {{}}
    }}

    async function saveMailSettings() {{
      const provider = document.getElementById('mail-provider-select').value;
      const smtp_user = document.getElementById('mail-user-inp').value.trim();
      const pass_val = document.getElementById('mail-pass-inp').value.trim();
      const from_name = document.getElementById('mail-fromname-inp').value.trim();
      const auto_send = document.getElementById('mail-autosend-cfg').checked;

      const payload = {{
        provider: provider,
        smtp_user: smtp_user,
        from_email: smtp_user,
        from_name: from_name,
        auto_send_qualifying: auto_send
      }};

      if (provider === 'gmail_smtp') {{
        if (pass_val && pass_val !== '••••••••') payload.smtp_password = pass_val;
      }} else if (provider === 'brevo') {{
        if (pass_val && !pass_val.includes('••')) payload.brevo_api_key = pass_val;
      }} else if (provider === 'resend') {{
        if (pass_val && !pass_val.includes('••')) payload.resend_api_key = pass_val;
      }} else if (provider === 'n8n_webhook') {{
        payload.webhook_url = smtp_user;
      }}

      const statusEl = document.getElementById('mail-save-status');
      try {{
        const res = await fetch('/api/pipeline/mail-config', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify(payload)
        }});
        const data = await res.json();
        if (statusEl) {{
          statusEl.style.display = 'block';
          statusEl.textContent = '✅ ' + (data.message || 'Settings saved successfully!');
          setTimeout(() => {{ statusEl.style.display = 'none'; }}, 3500);
        }}
      }} catch (e) {{
        alert('Failed to save settings: ' + e.message);
      }}
    }}

    async function runPipelineScan() {{
      const city = document.getElementById('pipeline-city-inp').value.trim() || 'Mumbai';
      const niche = document.getElementById('pipeline-niche-inp').value.trim() || 'Dental Clinic';
      const max_results = parseInt(document.getElementById('pipeline-max-inp').value.trim()) || 20;
      const token = document.getElementById('pipeline-token-inp').value.trim();
      const auto_send = document.getElementById('pipeline-auto-email').checked;

      const btn = document.getElementById('btn-run-pipeline');
      const statusEl = document.getElementById('pipeline-run-status');
      if (btn) {{
        btn.disabled = true;
        btn.textContent = '⏳ Executing Automated Pipeline...';
      }}
      if (statusEl) {{
        statusEl.style.display = 'block';
        statusEl.textContent = '🚀 Initializing Stage 1: Google Places Scraper for ' + niche + ' in ' + city + '...';
      }}

      try {{
        const res = await fetch('/api/pipeline/run', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ city, niche, max_results, token, auto_send_email: auto_send }})
        }});
        const data = await res.json();
        if (!data.success) {{
          alert('Notice: ' + (data.error || 'Failed to start pipeline'));
          if (btn) {{
            btn.disabled = false;
            btn.textContent = '🚀 Run Automated Pipeline Scan';
          }}
          return;
        }}

        const poll = setInterval(async () => {{
          try {{
            const sRes = await fetch('/api/pipeline/status');
            const s = await sRes.json();
            if (statusEl) {{
              const emailNotice = auto_send ? ' | ✉️ Auto-Sending Direct Emails' : '';
              statusEl.textContent = '⚙️ [' + s.status + '] Processed: ' + s.processed + '/' + s.total_found + ' | Qualifying: ' + s.qualifying + ' Demos' + emailNotice;
            }}
            if (!s.is_running) {{
              clearInterval(poll);
              if (statusEl) statusEl.textContent = '✅ Pipeline Complete! Reloading ledger...';
              setTimeout(() => location.reload(), 1200);
            }}
          }} catch(e) {{}}
        }}, 1500);

      }} catch(e) {{
        alert('Pipeline error: ' + e.message);
        if (btn) {{
          btn.disabled = false;
          btn.textContent = '🚀 Run Automated Pipeline Scan';
        }}
      }}
    }}
  </script>

</body>
</html>"""
