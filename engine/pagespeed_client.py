"""
LeakGrader.com - Google PageSpeed Insights API Client
Fetches real Core Web Vitals and Lighthouse category scores for mobile and desktop.
Includes:
1. 24-hour disk/file cache per domain.
2. Optional PAGESPEED_API_KEY support (never printed or logged).
3. Concurrent mobile + desktop fetching.
4. SSRF protection: validates target before outbound call.
5. Graceful fallback on rate limits (429), timeouts, or 5xx errors.
"""

import os
import re
import json
import time
import urllib.request
import urllib.parse
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from engine.security_guard import validate_url_ssrf_safe

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
CACHE_FILE = os.path.join(CACHE_DIR, "pagespeed_cache.json")
CACHE_TTL = 86400  # 24 hours in seconds

class PageSpeedClient:
    def __init__(self, api_key: str = None, timeout: int = 40):
        self.api_key = self._resolve_api_key(api_key)
        self.timeout = timeout
        self._ensure_cache_dir()
        # Diagnostic: server-side log, no key value exposed
        print("PSI: API key present" if self.api_key else "PSI: no API key", flush=True)

    @staticmethod
    def _resolve_api_key(passed_key: str = None) -> str:
        key = (
            passed_key
            or os.environ.get("PAGESPEED_API_KEY")
            or os.environ.get("GOOGLE_PAGESPEED_API_KEY")
            or os.environ.get("PAGE_SPEED_API_KEY")
            or os.environ.get("GOOGLE_API_KEY")
            or ""
        )
        return key.strip().strip('"').strip("'")

    def _ensure_cache_dir(self):
        try:
            if not os.path.exists(CACHE_DIR):
                os.makedirs(CACHE_DIR, exist_ok=True)
            if not os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump({}, f)
        except Exception:
            pass

    def clear_cache(self, domain: str = None):
        """Clears cache entries for a specific domain or all domains."""
        try:
            if not os.path.exists(CACHE_FILE):
                return
            if domain is None:
                with open(CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump({}, f)
            else:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    cache = json.load(f)
                clean_dom = domain.lower().replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
                if clean_dom in cache:
                    del cache[clean_dom]
                    with open(CACHE_FILE, "w", encoding="utf-8") as f:
                        json.dump(cache, f)
        except Exception:
            pass

    def _read_cache(self, domain: str) -> dict:
        try:
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    cache = json.load(f)
                    entry = cache.get(domain)
                    if entry and (time.time() - entry.get("cached_at", 0) < CACHE_TTL):
                        return entry.get("data")
        except Exception:
            pass
        return None

    def _write_cache(self, domain: str, data: dict):
        try:
            cache = {}
            if os.path.exists(CACHE_FILE):
                try:
                    with open(CACHE_FILE, "r", encoding="utf-8") as f:
                        cache = json.load(f)
                except Exception:
                    cache = {}
            cache[domain] = {
                "cached_at": time.time(),
                "data": data
            }
            # Trim cache if too large (keep last 200 entries)
            if len(cache) > 200:
                oldest_keys = sorted(cache.keys(), key=lambda k: cache[k].get("cached_at", 0))[:50]
                for k in oldest_keys:
                    del cache[k]
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache, f)
        except Exception:
            pass

    def _fetch_strategy(self, url: str, strategy: str = "mobile") -> dict:
        """
        Calls Google PageSpeed Insights API for a specific strategy (mobile or desktop).
        Appends PAGESPEED_API_KEY when available and executes with proper timeout.
        """
        api_key = self._resolve_api_key(self.api_key)
        query_params = [
            ("url", url),
            ("strategy", strategy),
            ("category", "performance"),
            ("category", "accessibility"),
            ("category", "seo")
        ]
        if api_key:
            query_params.append(("key", api_key))

        encoded_url = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?" + urllib.parse.urlencode(query_params)
        
        last_err = None
        for attempt in range(2):
            try:
                req = urllib.request.Request(
                    encoded_url,
                    headers={"User-Agent": "LeakGrader-RealDataEngine/2.0"}
                )
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    if resp.status == 200:
                        raw_data = json.loads(resp.read().decode("utf-8"))
                        return self._parse_psi_response(raw_data, strategy)
            except urllib.error.HTTPError as e:
                err_snippet = ""
                try:
                    err_snippet = e.read().decode("utf-8", errors="ignore")[:300]
                except Exception:
                    pass
                print(f"PSI: {strategy} HTTP {e.code} for {url} - {err_snippet}", flush=True)
                last_err = f"HTTP {e.code}"
                # Retry once only on 5xx errors
                if e.code >= 500 and attempt == 0:
                    time.sleep(1.0)
                    continue
                break
            except Exception as e:
                err_type = type(e).__name__
                err_msg = str(e)
                print(f"PSI: {strategy} exception for {url} - {err_type}: {err_msg}", flush=True)
                last_err = f"{err_type}: {err_msg}" if err_msg else err_type
                break

        return {
            "status": "unavailable",
            "error": last_err or "PageSpeed API request failed or timed out",
            "strategy": strategy,
            "performance_score": None,
            "accessibility_score": None,
            "seo_score": None,
            "best_practices_score": None,
            "core_web_vitals": self._empty_cwv()
        }

    def _empty_cwv(self) -> dict:
        return {
            "lcp": {"value": None, "display": "Unavailable", "status": "PENDING", "threshold": "<= 2.5s"},
            "cls": {"value": None, "display": "Unavailable", "status": "PENDING", "threshold": "<= 0.1"},
            "tbt": {"value": None, "display": "Unavailable", "status": "PENDING", "threshold": "<= 200ms"},
            "fcp": {"value": None, "display": "Unavailable", "status": "PENDING", "threshold": "<= 1.8s"},
            "speed_index": {"value": None, "display": "Unavailable", "status": "PENDING", "threshold": "<= 3.4s"}
        }

    def _parse_psi_response(self, data: dict, strategy: str) -> dict:
        lh = data.get("lighthouseResult", {})
        cats = lh.get("categories", {})
        audits = lh.get("audits", {})

        def get_cat_score(cat_id):
            c = cats.get(cat_id)
            if c and c.get("score") is not None:
                return round(c["score"] * 100)
            return None

        perf = get_cat_score("performance")
        a11y = get_cat_score("accessibility")
        seo = get_cat_score("seo")
        bp = get_cat_score("best-practices")

        # Extract Core Web Vitals
        def audit_data(audit_id, good_th, ni_th, unit="s", higher_better=False):
            aud = audits.get(audit_id, {})
            val = aud.get("numericValue")
            disp = aud.get("displayValue") or "N/A"
            status = "NEEDS_IMPROVEMENT"
            if val is not None:
                if not higher_better:
                    if val <= good_th:
                        status = "GOOD"
                    elif val <= ni_th:
                        status = "NEEDS_IMPROVEMENT"
                    else:
                        status = "POOR"
                else:
                    if val >= good_th:
                        status = "GOOD"
                    elif val >= ni_th:
                        status = "NEEDS_IMPROVEMENT"
                    else:
                        status = "POOR"
            elif disp != "N/A":
                status = "PASS" if "s" in disp and float(re.sub(r"[^0-9.]", "", disp) or "99") <= good_th else "WARN"
            return {"value": val, "display": disp, "status": status}

        # Thresholds from Google Web Vitals guidelines:
        # LCP: <= 2500ms (Good), <= 4000ms (Needs Improvement), > 4000ms (Poor)
        lcp = audit_data("largest-contentful-paint", 2500, 4000, "ms")
        lcp["threshold"] = "<= 2.5s"

        # CLS: <= 0.1 (Good), <= 0.25 (Needs Improvement), > 0.25 (Poor)
        cls = audit_data("cumulative-layout-shift", 0.1, 0.25, "")
        cls["threshold"] = "<= 0.1"

        # TBT: <= 200ms (Good), <= 600ms (Needs Improvement), > 600ms (Poor)
        tbt = audit_data("total-blocking-time", 200, 600, "ms")
        tbt["threshold"] = "<= 200ms"

        # FCP: <= 1800ms (Good), <= 3000ms (Needs Improvement), > 3000ms (Poor)
        fcp = audit_data("first-contentful-paint", 1800, 3000, "ms")
        fcp["threshold"] = "<= 1.8s"

        # Speed Index: <= 3400ms (Good), <= 5800ms (Needs Improvement)
        si = audit_data("speed-index", 3400, 5800, "ms")
        si["threshold"] = "<= 3.4s"

        return {
            "status": "success",
            "strategy": strategy,
            "performance_score": perf,
            "accessibility_score": a11y,
            "seo_score": seo,
            "best_practices_score": bp,
            "core_web_vitals": {
                "lcp": lcp,
                "cls": cls,
                "tbt": tbt,
                "fcp": fcp,
                "speed_index": si
            }
        }

    def get_pagespeed_metrics(self, domain_or_url: str, bypass_cache: bool = False) -> dict:
        """
        Retrieves PageSpeed metrics for mobile and desktop.
        1. Validates SSRF safety BEFORE making any request.
        2. Checks 24h cache (unless bypass_cache=True).
        3. Executes concurrent mobile and desktop queries.
        4. Caches and returns normalized payload.
        """
        raw = str(domain_or_url or "").strip()
        if not raw:
            return {"status": "error", "error": "empty_domain", "is_real_psi": False}

        # Dynamically refresh API key to pick up any environment variable updates
        self.api_key = self._resolve_api_key(self.api_key)
        print("PSI: API key present" if self.api_key else "PSI: no API key", flush=True)

        # Normalize URL
        url = raw if raw.startswith("http://") or raw.startswith("https://") else f"https://{raw}"
        domain = raw.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0].lower()

        # SSRF PRE-FLIGHT GUARD: Strictly block private/internal IPs before PSI
        is_safe, safe_target, ssrf_err = validate_url_ssrf_safe(url)
        if not is_safe:
            return {
                "status": "blocked",
                "error": f"SSRF target prohibited: {ssrf_err}",
                "is_real_psi": False,
                "domain": domain
            }

        # Check 24-hour cache
        if not bypass_cache:
            cached = self._read_cache(domain)
            if cached:
                cached["from_cache"] = True
                return cached

        # Fetch mobile & desktop in parallel with robust timeouts
        try:
            with ThreadPoolExecutor(max_workers=2) as executor:
                mobile_future = executor.submit(self._fetch_strategy, safe_target, "mobile")
                desktop_future = executor.submit(self._fetch_strategy, safe_target, "desktop")

                mobile_data = mobile_future.result(timeout=self.timeout + 10)
                desktop_data = desktop_future.result(timeout=self.timeout + 10)
        except Exception as e:
            err_type = type(e).__name__
            err_msg = str(e)
            err_desc = f"{err_type}: {err_msg}" if err_msg else err_type
            mobile_data = {
                "status": "unavailable",
                "error": err_desc,
                "strategy": "mobile",
                "performance_score": None,
                "accessibility_score": None,
                "seo_score": None,
                "best_practices_score": None,
                "core_web_vitals": self._empty_cwv()
            }
            desktop_data = {
                "status": "unavailable",
                "error": err_desc,
                "strategy": "desktop",
                "performance_score": None,
                "accessibility_score": None,
                "seo_score": None,
                "best_practices_score": None,
                "core_web_vitals": self._empty_cwv()
            }

        is_real = (mobile_data.get("status") == "success" or desktop_data.get("status") == "success")
        
        if is_real:
            note = "Verified real Google PageSpeed Insights data"
        else:
            combined_err = f"{mobile_data.get('error', '')} {desktop_data.get('error', '')}"
            if "429" in combined_err:
                note = "Google PageSpeed Insights API quota exceeded or rate-limited. Speed metrics marked pending."
            elif "Timeout" in combined_err or "timed out" in combined_err.lower():
                note = "Google PageSpeed Insights analysis timed out for this URL. Speed metrics marked pending."
            elif "403" in combined_err:
                note = "Google PageSpeed Insights API key unauthorized or API disabled. Speed metrics marked pending."
            else:
                note = "Google PageSpeed Insights API temporarily unavailable. Speed metrics marked pending."

        result = {
            "status": "success" if is_real else "unavailable",
            "is_real_psi": is_real,
            "domain": domain,
            "url": safe_target,
            "mobile": mobile_data,
            "desktop": desktop_data,
            "note": note,
            "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S UTC")
        }

        # Write to cache if succeeded
        if is_real:
            self._write_cache(domain, result)

        return result
