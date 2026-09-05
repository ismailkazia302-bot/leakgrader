"""
LeakGrader.com - Competitor Spy & Head-to-Head Battlecard Agent
Analyzes and benchmarks two competing businesses side-by-side:
1. Live Tech-Stack & Lead Capture Friction (CMS, Forms, WhatsApp/Chat Closer).
2. Estimated Revenue Loss & AI Readiness Score Comparison.
3. Decides the Head-to-Head Winner and tactical battle recommendations to steal market share.
"""

import json
import time
import hashlib
from engine.audit_engine import ViralAuditEngine
from engine.realtime_enricher import RealtimeWebsiteEnricher

class CompetitorSpyAgent:
    def __init__(self, api_key: str = "", model: str = "gemini-1.5-flash"):
        self.audit_engine = ViralAuditEngine(api_key=api_key, model=model)
        self.enricher = RealtimeWebsiteEnricher(timeout=4)

    def run_battlecard(self, my_domain: str, competitor_domain: str, industry_hint: str = "") -> dict:
        """
        Executes head-to-head comparison between client site and competitor site.
        """
        # 1. Audit both domains in parallel
        my_audit = self.audit_engine.run_instant_audit(my_domain, industry_hint)
        comp_audit = self.audit_engine.run_instant_audit(competitor_domain, industry_hint)

        # 2. Extract key metrics
        my_score = my_audit.get("ai_readiness_score", 70)
        comp_score = comp_audit.get("ai_readiness_score", 65)

        # Winner evaluation
        if my_score >= comp_score:
            winner = my_audit["company_name"]
            leader_tag = "CLIENT_ADVANTAGE"
            summary_insight = f"{my_audit['company_name']} leads by +{my_score - comp_score} AI Readiness points over {comp_audit['company_name']}."
        else:
            winner = comp_audit["company_name"]
            leader_tag = "COMPETITOR_ADVANTAGE"
            summary_insight = f"{comp_audit['company_name']} leads by +{comp_score - my_score} AI Readiness points. Deploying 24/7 AI Closer will immediately flip this lead."

        # Battlecard comparison metrics
        comparison_points = [
            {
                "category": "24/7 WhatsApp AI Closer",
                "my_status": "Active / Ready" if my_audit.get("has_whatsapp") else "Missing (High Dropoff)",
                "comp_status": "Active / Ready" if comp_audit.get("has_whatsapp") else "Missing (High Dropoff)",
                "impact": "Captures 42% more mobile visitors after business hours"
            },
            {
                "category": "Lead Form Friction",
                "my_status": f"{my_audit.get('form_friction_fields', 5)} Input Fields",
                "comp_status": f"{comp_audit.get('form_friction_fields', 6)} Input Fields",
                "impact": "1-click conversational AI converts 3x better than static forms"
            },
            {
                "category": "Estimated Monthly Loss",
                "my_status": my_audit.get("estimated_monthly_leak", "$35,000/mo"),
                "comp_status": comp_audit.get("estimated_monthly_leak", "$45,000/mo"),
                "impact": "Revenue recoverable via instant 30-sec response pipelines"
            }
        ]

        # Actionable battle recommendations
        tactical_advantages = [
            f"Deploy LeakGrader 24/7 AI Sales Closer to capture {comp_audit['company_name']}'s after-hours drop-off traffic.",
            f"Replace static contact forms with 1-click WhatsApp qualifier to reduce bounce rate.",
            f"Embed Verified LeakGrader Badge to display certified AI readiness to prospective clients."
        ]

        battle_seed = int(hashlib.md5((my_domain + competitor_domain).lower().encode('utf-8')).hexdigest()[:8], 16)
        battle_id = f"battle_{battle_seed % 1000000}"

        return {
            "battle_id": battle_id,
            "domain": my_domain,
            "my_domain": my_domain,
            "competitor": competitor_domain,
            "competitor_domain": competitor_domain,
            "leak_score_diff": abs(my_score - comp_score),
            "strengths": tactical_advantages,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "my_business": my_audit,
            "competitor_business": comp_audit,
            "winner": winner,
            "leader_tag": leader_tag,
            "summary_insight": summary_insight,
            "comparison_matrix": comparison_points,
            "tactical_advantages": tactical_advantages,
            "share_url": f"https://leakgrader.com/battle/{battle_id}"
        }
