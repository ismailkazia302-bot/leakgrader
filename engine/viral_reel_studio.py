"""
LeakGrader.com - Autonomous Viral Reels, TikTok & Shorts Studio Engine
Researches trending business/tech angles, plans educational hooks,
and generates complete production-ready vertical (9:16) video scripts,
captions, hashtags, and dispatches to Instagram, Facebook, TikTok & YouTube.
"""

import json
import time
import os
import urllib.request
import urllib.parse

DEFAULT_CREDS = {
    "instagram": {"access_token": "", "instagram_account_id": "", "status": "NOT_CONFIGURED"},
    "facebook": {"page_access_token": "", "page_id": "", "status": "NOT_CONFIGURED"},
    "tiktok": {"access_token": "", "open_id": "", "status": "NOT_CONFIGURED"},
    "youtube": {"client_id": "", "client_secret": "", "refresh_token": "", "status": "NOT_CONFIGURED"},
    "auto_publisher_webhook": ""
}

VIRAL_TREND_CONCEPTS = [
    {
        "niche": "Luxury Real Estate & High-Ticket Brokerages",
        "angle": "The 10 PM Millionaire Investor Dropoff",
        "hook": "If you run a luxury real estate agency, stop scrolling. You are losing $50k+ every single month.",
        "industry_education": "We audited 50 top property portals. 71% of international investors browse between 9 PM and 2 AM. When they click Contact Us and see a 5-field form, 80% close the tab and buy from the first agency with a 24/7 WhatsApp bot.",
        "demo_leakgrader": "Open LeakGrader.com, type in your agency domain. In 10 seconds, it calculates your exact after-hours lead leak and gives you a 30-second AI closer bot.",
        "cta": "Go to LeakGrader.com right now and scan your website for free.",
        "hashtags": ["#realestateinvesting", "#luxuryliving", "#proptech", "#aitools", "#salesautomation", "#businesstips", "#leadgeneration"]
    },
    {
        "niche": "Cosmetic & Private Dental Clinics",
        "angle": "Why Dental Contact Forms Are Losing $30k/mo in Implants",
        "hook": "Dental practice owners: your contact form is secretly killing your highest-paying patients.",
        "industry_education": "Patients needing $5,000 implants browse at night after work. If you make them wait 12 hours for an email reply, they call the clinic across town. The first practice to reply within 30 seconds wins 78% of bookings.",
        "demo_leakgrader": "Put your clinic website into LeakGrader.com. It tests your mobile response speed and shows you the exact dollar revenue you lost this week.",
        "cta": "Scan your dental or clinic website free on LeakGrader.com.",
        "hashtags": ["#dentalmarketing", "#clinicgrowth", "#healthcaretech", "#smallbusinesstips", "#leadgen", "#entrepreneurship"]
    },
    {
        "niche": "B2B SaaS & Tech Startups",
        "angle": "The 30-Second Rule That Tripled Demo Bookings",
        "hook": "Why 78% of SaaS website visitors never book a demo.",
        "industry_education": "Traditional SaaS sites force buyers through Book a Demo calendars with 8 qualifying fields. Friction destroys conversion. An interactive 30-second conversational AI closer converts at 14.8% vs 2.1% for static forms.",
        "demo_leakgrader": "LeakGrader.com audits your SaaS funnel in 10 seconds and estimates your monthly pipeline dropoff.",
        "cta": "Test your domain on LeakGrader.com — 100% free.",
        "hashtags": ["#saas", "#b2bmarketing", "#startuptips", "#conversionrateoptimization", "#growthhacking", "#aitools"]
    },
    {
        "niche": "Home Services, Solar & Emergency Contractors",
        "angle": "The $20,000 Burst Pipe Problem",
        "hook": "If you run a roofing, plumbing or solar company, this 1 mistake costs you $20,000 a month.",
        "industry_education": "When an emergency happens, homeowners call 3 contractors in a row. The first contractor whose phone or 24/7 WhatsApp AI answers in under 1 minute gets the $10,000 job 100% of the time. Voicemails are where revenue goes to die.",
        "demo_leakgrader": "Check your contractor site on LeakGrader.com. It simulates an after-hours emergency inquiry and grades your capture speed.",
        "cta": "Link is in bio — run your free leak test on LeakGrader.com.",
        "hashtags": ["#contractorlife", "#roofingmarketing", "#hvacservice", "#localbusiness", "#automationtools", "#businesstips"]
    },
    {
        "niche": "Digital Marketing & Web Agencies",
        "angle": "How Agencies Land $2,000/mo Retainers in 10 Seconds",
        "hook": "Stop pitching website redesigns. Pitch Revenue Leak Recovery instead.",
        "industry_education": "Clients do not care about pretty websites anymore. They care about lost money. If you show a business owner an audit showing they lose $35,000/month in missed mobile leads, they gladly pay $1,500 for you to fix it with an AI sales closer.",
        "demo_leakgrader": "Use LeakGrader.com to generate instant client battlecards and 15-page revenue leak dossiers in 10 seconds.",
        "cta": "Try LeakGrader.com free today and close your next agency client.",
        "hashtags": ["#agencyowner", "#digitalagency", "#freelancetips", "#b2bsales", "#aitools2026", "#sidehustle"]
    }
]

class ViralReelStudioEngine:
    def __init__(self, storage_dir: str = None, config_path: str = None):
        self.storage_dir = storage_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "storage")
        self.config_path = config_path or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config", "reel_credentials.json")
        os.makedirs(self.storage_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        self.reels_file = os.path.join(self.storage_dir, "viral_reels_vault.json")
        self.reels = self._load_data(self.reels_file)
        self.creds = self._load_creds()

        if not self.reels:
            for c in VIRAL_TREND_CONCEPTS[:3]:
                self.generate_reel(c)

    def _load_data(self, path: str) -> list:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_data(self, path: str, data: list):
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[ViralReelStudio] Error saving data: {e}")

    def _load_creds(self) -> dict:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return dict(DEFAULT_CREDS)
        return dict(DEFAULT_CREDS)

    def save_credentials(self, new_creds: dict) -> dict:
        self.creds.update(new_creds)
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.creds, f, indent=2)
            return {"status": "SUCCESS", "message": "Social media credentials updated successfully."}
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}

    def generate_reel(self, concept: dict = None) -> dict:
        if not concept:
            idx = len(self.reels) % len(VIRAL_TREND_CONCEPTS)
            concept = VIRAL_TREND_CONCEPTS[idx]

        reel_id = f"reel_{int(time.time())}_{len(self.reels) + 1}"
        now = time.strftime("%Y-%m-%d %H:%M:%S UTC")

        voiceover = f"{concept['hook']} {concept['industry_education']} {concept['demo_leakgrader']} {concept['cta']}"
        tags_str = " ".join(concept["hashtags"])
        caption = f"🚨 {concept['angle']}\n\n{concept['industry_education']}\n\n⚡ Test your website's leak score for free at LeakGrader.com\n\n{tags_str}"

        reel_entry = {
            "id": reel_id,
            "created_at": now,
            "topic_niche": concept["niche"],
            "angle": concept["angle"],
            "status": "READY_TO_PUBLISH",
            "duration_estimate": "28 seconds",
            "aspect_ratio": "9:16 (Vertical Reel/Short)",
            "script_storyboard": {
                "scene_1_hook_0_3s": {
                    "duration": "0 - 3s",
                    "screen_visual": "⚡ Bold red text overlay: " + concept["hook"][:45] + "... Phone screen vibrating with missed leads.",
                    "voiceover": concept["hook"],
                    "audio_soundtrack": "Trending Tech Mystery Beat (Fast bpm)"
                },
                "scene_2_problem_3_12s": {
                    "duration": "3 - 12s",
                    "screen_visual": "📉 Red graph showing 78% dropoff on mobile forms after 6 PM. Clock ticking to 10 PM.",
                    "voiceover": concept["industry_education"],
                    "on_screen_callout": "68% of Inbound Leads Arrive After-Hours"
                },
                "scene_3_solution_12_22s": {
                    "duration": "12 - 22s",
                    "screen_visual": "💻 Screen recording of LeakGrader.com typing domain -> 10-second instant diagnostic calculation showing $35,000/mo Leak.",
                    "voiceover": concept["demo_leakgrader"],
                    "on_screen_callout": "Instant 10s Diagnostic @ LeakGrader.com"
                },
                "scene_4_cta_22_28s": {
                    "duration": "22 - 28s",
                    "screen_visual": "📲 Green glowing button: Test Your Website Free at LeakGrader.com (Link in Bio / Description).",
                    "voiceover": concept["cta"],
                    "on_screen_callout": "Tap Link in Bio 🔗"
                }
            },
            "voiceover_full_transcript": voiceover,
            "caption": caption,
            "hashtags": concept["hashtags"],
            "platforms": ["Instagram Reels", "Facebook Reels", "TikTok", "YouTube Shorts"],
            "dispatch_status": {
                "instagram": "QUEUED",
                "facebook": "QUEUED",
                "tiktok": "QUEUED",
                "youtube": "QUEUED"
            }
        }

        self.reels.insert(0, reel_entry)
        if len(self.reels) > 50:
            self.reels = self.reels[:50]
        self._save_data(self.reels_file, self.reels)
        return reel_entry

    def dispatch_reel(self, reel_id: str) -> dict:
        reel = next((r for r in self.reels if r["id"] == reel_id), None)
        if not reel:
            return {"status": "ERROR", "error": "Reel not found"}

        webhook = self.creds.get("auto_publisher_webhook", "")
        dispatch_report = {
            "reel_id": reel_id,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "webhook_triggered": False
        }

        if webhook:
            try:
                payload = json.dumps({
                    "event": "NEW_VIRAL_REEL_READY",
                    "reel": reel,
                    "media_spec": "9:16_VERTICAL_VIDEO",
                    "caption": reel["caption"],
                    "hashtags": reel["hashtags"],
                    "voiceover": reel["voiceover_full_transcript"]
                }).encode("utf-8")
                req = urllib.request.Request(webhook, data=payload, headers={"Content-Type": "application/json"})
                resp = urllib.request.urlopen(req, timeout=8)
                dispatch_report["webhook_triggered"] = True
                dispatch_report["webhook_status"] = resp.status
            except Exception as e:
                dispatch_report["webhook_error"] = str(e)

        reel["status"] = "DISPATCHED_TO_AUTO_PUBLISHER"
        reel["dispatched_at"] = time.strftime("%Y-%m-%d %H:%M:%S UTC")
        self._save_data(self.reels_file, self.reels)

        return {"status": "SUCCESS", "report": dispatch_report, "reel": reel}

    def get_feed(self) -> dict:
        return {
            "total_reels": len(self.reels),
            "latest_reel": self.reels[0] if self.reels else {},
            "all_reels": self.reels,
            "credentials_summary": {
                "instagram": bool(self.creds.get("instagram", {}).get("access_token")),
                "facebook": bool(self.creds.get("facebook", {}).get("page_access_token")),
                "tiktok": bool(self.creds.get("tiktok", {}).get("access_token")),
                "youtube": bool(self.creds.get("youtube", {}).get("client_id")),
                "webhook": bool(self.creds.get("auto_publisher_webhook"))
            }
        }
