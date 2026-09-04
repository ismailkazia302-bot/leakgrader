"""
LeakGrader.com - Master 100% Autonomous Growth & SEO Controller
Runs 100% Hands-Free for the Founder:
1. On-Page SEO & Schema Validation.
2. Off-Page High-DA Backlink Submissions & IndexNow Broadcasting.
3. Autonomous B2B Outbound Campaigns (Direct Email & WhatsApp Teardowns to Decision-Makers).
"""

import json
import time
import os
from engine.onpage_seo import OnPageSEOEngine
from engine.offpage_seo import OffPageSEOEngine
from engine.auto_outreach_bot import AutonomousOutreachEngine
from engine.social_auto_poster import SocialAutoPoster

class GrowthAndIndexingAgent:
    def __init__(self, base_url: str = "https://leakgrader.com"):
        self.base_url = base_url.rstrip('/')
        self.onpage = OnPageSEOEngine(base_url=self.base_url)
        self.offpage = OffPageSEOEngine(base_url=self.base_url)
        self.outreach = AutonomousOutreachEngine()
        self.social_poster = SocialAutoPoster(base_url=self.base_url)

    def run_full_seo_cycle(self, target_keyword: str = "Website Revenue Leak Scanner") -> dict:
        """
        Executes 100% autonomous growth sprint: SEO + Backlinks + Outbound Dispatches + Social Auto-Posting.
        """
        onpage_report = self.onpage.audit_and_optimize_page(target_keyword=target_keyword)
        offpage_report = self.offpage.execute_offpage_sprint(target_url=f"{self.base_url}/")
        outreach_report = self.outreach.run_autonomous_outreach_cycle()
        try:
            social_report = self.social_poster.run_social_cycle()
        except Exception as e:
            social_report = {"status": "ERROR", "error": str(e)}

        return {
            "status": "100_PERCENT_HANDS_FREE_SPRINT_SUCCESS",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "on_page_seo": onpage_report,
            "off_page_seo": offpage_report,
            "autonomous_outbound": outreach_report,
            "social_auto_poster": social_report
        }

    # Backward compatibility alias
    def submit_to_indexnow(self, urls: list = None) -> dict:
        cycle = self.run_full_seo_cycle()
        res = cycle["off_page_seo"]
        res["autonomous_outreach"] = cycle["autonomous_outbound"]
        return res
