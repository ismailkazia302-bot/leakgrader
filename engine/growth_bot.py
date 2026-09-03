"""
LeakGrader.com - Master Autonomous SEO Controller (On-Page + Off-Page Dual Engine)
"""

import json
import time
import os
from engine.onpage_seo import OnPageSEOEngine
from engine.offpage_seo import OffPageSEOEngine

class GrowthAndIndexingAgent:
    def __init__(self, base_url: str = "https://leakgrader.com"):
        self.base_url = base_url.rstrip('/')
        self.onpage = OnPageSEOEngine(base_url=self.base_url)
        self.offpage = OffPageSEOEngine(base_url=self.base_url)

    def run_full_seo_cycle(self, target_keyword: str = "Website Revenue Leak Scanner") -> dict:
        """
        Runs both On-Page SEO audit & Off-Page backlink/indexing sprint.
        """
        onpage_report = self.onpage.audit_and_optimize_page(target_keyword=target_keyword)
        offpage_report = self.offpage.execute_offpage_sprint(target_url=f"{self.base_url}/")

        return {
            "status": "FULL_DUAL_SEO_CYCLE_COMPLETED",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "on_page_seo": onpage_report,
            "off_page_seo": offpage_report
        }

    # Backward compatibility alias
    def submit_to_indexnow(self, urls: list = None) -> dict:
        return self.run_full_seo_cycle()["off_page_seo"]
