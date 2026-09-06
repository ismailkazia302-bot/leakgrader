"""
LeakGrader.com - Local Business Pipeline Classifier Engine
Evaluates scraped businesses against Stage 3 criteria:
1. No Website Check
2. SSL Check (Fail if http-only or SSL broken)
3. Mobile Viewport Check (Fail if no viewport meta / non-responsive)
4. Design Age Check (Fail if table layouts, obsolete tags, old copyright <=2021)
5. Load Time Check (Fail if latency > 3.5 seconds)
6. AI Visual Judgment (Aesthetic, typography, structure read)

Decision:
- "No Website" -> Qualifies for Redesign (Stage 4)
- "Outdated" -> Qualifies for Redesign (Stage 4)
- "Skip" -> Modern site, pass
"""

import urllib.request
import urllib.parse
import re
import time
import ssl

class PipelineClassifier:
    def __init__(self, timeout: float = 6.0):
        self.timeout = timeout

    def classify_business(self, business: dict) -> dict:
        """
        Executes Stage 3 classification rules on a business record.
        Returns a dict with updated check fields and final Status.
        """
        raw_website = (business.get("Website") or business.get("website") or "").strip()

        # Rule 1: No Website
        if not raw_website or raw_website.lower() in ["none", "n/a", "null", "no website", "-", ""]:
            return {
                "SSL Check": "N/A",
                "Mobile Check": "N/A",
                "Design Age Check": "N/A",
                "Load Time Check": "N/A",
                "AI Visual Judgment": "Missing Digital Presence",
                "Status": "No Website",
                "Qualifying": True,
                "FailReasons": ["Zero digital footprint: No website found on Google Maps"]
            }

        # Format URL
        url = raw_website
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url

        fail_reasons = []

        # 1. SSL Check
        ssl_pass, ssl_detail = self._check_ssl(url)
        ssl_check = "Pass" if ssl_pass else "Fail"
        if not ssl_pass:
            fail_reasons.append(f"SSL Check Failed: {ssl_detail}")

        # 2, 3, 4, 5. Fetch website and measure load time
        fetch_res = self._fetch_page_content(url)
        
        load_time_sec = fetch_res.get("load_time", 0.0)
        load_time_pass = fetch_res.get("success", False) and (load_time_sec <= 3.5)
        load_time_check = f"Pass ({load_time_sec:.2f}s)" if load_time_pass else f"Fail ({load_time_sec:.2f}s)"
        if not load_time_pass:
            fail_reasons.append(f"Slow Load Latency: {load_time_sec:.2f}s exceeds 3.5s speed benchmark")

        html = fetch_res.get("html", "")

        # Mobile Viewport Check
        mobile_pass, mobile_detail = self._check_mobile(html)
        mobile_check = "Pass" if mobile_pass else "Fail"
        if not mobile_pass:
            fail_reasons.append(f"Mobile Check Failed: {mobile_detail}")

        # Design Age Check
        age_pass, age_detail = self._check_design_age(html)
        age_check = "Pass" if age_pass else "Fail"
        if not age_pass:
            fail_reasons.append(f"Design Age Check Failed: {age_detail}")

        # AI Visual & Structural Judgment
        ai_judgment, ai_detail = self._ai_visual_judgment(html, fail_reasons)
        if ai_judgment == "Outdated":
            fail_reasons.append(f"AI Visual Audit: {ai_detail}")

        # Final Status Decision:
        # Outdated if any check failed OR AI judgment is Outdated
        is_outdated = (
            ssl_check == "Fail" or 
            mobile_check == "Fail" or 
            age_check == "Fail" or 
            load_time_check.startswith("Fail") or 
            ai_judgment == "Outdated"
        )

        status = "Outdated" if is_outdated else "Skip"

        return {
            "SSL Check": ssl_check,
            "Mobile Check": mobile_check,
            "Design Age Check": age_check,
            "Load Time Check": load_time_check,
            "AI Visual Judgment": ai_judgment,
            "Status": status,
            "Qualifying": (status in ["No Website", "Outdated"]),
            "FailReasons": fail_reasons
        }

    def _check_ssl(self, url: str) -> tuple:
        parsed = urllib.parse.urlparse(url)
        host = parsed.netloc.split(":")[0]
        if parsed.scheme == "http" and not url.startswith("https"):
            # Check if https upgrades
            https_url = "https://" + parsed.netloc + parsed.path
            try:
                ctx = ssl.create_default_context()
                req = urllib.request.Request(https_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, context=ctx, timeout=3.0) as r:
                    return (True, "HTTPS verified")
            except Exception:
                return (False, "HTTP only, no valid SSL certificate")

        try:
            ctx = ssl.create_default_context()
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, context=ctx, timeout=3.0) as r:
                return (True, "HTTPS secure")
        except Exception as e:
            return (False, f"SSL verification error: {str(e)[:40]}")

    def _fetch_page_content(self, url: str) -> dict:
        start = time.time()
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=self.timeout) as resp:
                elapsed = time.time() - start
                content = resp.read()
                # Decode with fallback
                try:
                    html = content.decode("utf-8")
                except UnicodeDecodeError:
                    html = content.decode("latin-1", errors="ignore")
                return {"success": True, "load_time": elapsed, "html": html}
        except Exception as e:
            elapsed = time.time() - start
            return {"success": False, "load_time": elapsed, "html": "", "error": str(e)}

    def _check_mobile(self, html: str) -> tuple:
        if not html:
            return (False, "Website unreachable or returned empty DOM")

        has_viewport = bool(re.search(r'<meta[^>]+name=["\']viewport["\']', html, re.I))
        has_media_query = bool(re.search(r'@media\s*\([^)]+width', html, re.I)) or ("responsive" in html.lower())

        if not has_viewport:
            return (False, "Missing viewport meta tag (fails mobile screen scaling)")
        
        return (True, "Viewport responsive meta configured")

    def _check_design_age(self, html: str) -> tuple:
        if not html:
            return (False, "Empty content")

        html_lower = html.lower()

        # Check for obsolete table layouts
        table_layout_count = len(re.findall(r'<table[^>]+(cellpadding|cellspacing|width=["\']100%["\'])', html_lower))
        if table_layout_count >= 2:
            return (False, "Obsolete table-based layout structure detected")

        # Obsolete tags
        obsolete_tags = ["<font", "<center>", "<marquee>", "<frameset>"]
        for tag in obsolete_tags:
            if tag in html_lower:
                return (False, f"Uses deprecated legacy HTML ({tag})")

        # Check footer copyright year
        years = re.findall(r'(?:copyright|©|\(c\))\s*(?:20\d\d[-–])?(20\d\d)', html_lower)
        if years:
            last_year = max([int(y) for y in years if y.isdigit()])
            if last_year <= 2021:
                return (False, f"Outdated copyright year ({last_year}) indicates abandoned website")

        return (True, "Modern markup signatures detected")

    def _ai_visual_judgment(self, html: str, existing_fails: list) -> tuple:
        """
        Heuristic / Structural AI read of visual aesthetics, typography, and friction.
        """
        if not html or len(existing_fails) >= 2:
            return ("Outdated", "Multiple fundamental design & latency failures")

        html_lower = html.lower()
        score = 100

        # Penalize for lack of modern CSS libraries/signatures
        modern_signatures = ["tailwind", "bootstrap", "flex", "grid", "rem", "calc", "svg", "webflow", "framer"]
        modern_found = sum(1 for s in modern_signatures if s in html_lower)
        if modern_found <= 1:
            score -= 30

        # Check for contact form friction (too many inputs or mailto link only)
        input_count = len(re.findall(r'<input', html_lower))
        if input_count >= 7:
            score -= 20  # High friction desktop contact form

        # Check for SSL and mobile presence
        if any("SSL" in f for f in existing_fails):
            score -= 25
        if any("Mobile" in f for f in existing_fails):
            score -= 30

        if score < 65:
            return ("Outdated", f"Cluttered legacy architecture, low modern styling score ({score}/100)")
        return ("Modern", f"Clean visual structure ({score}/100)")
