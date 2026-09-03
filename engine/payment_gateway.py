"""
LeakGrader.com - Automated Payment Gateway & Checkout Engine
Supports LemonSqueezy, Stripe, Direct Checkout Links, and Sandbox Simulation.
Handles:
- $9 Micro-Unlocks (Instant Full Diagnostic & Verified Leads)
- $79 / month Pro SaaS Subscriptions
- $1,500 High-Ticket Done-For-You AI Closer Deployments
"""

import json
import time
import os

PLANS = {
    "micro_audit": {
        "id": "plan_micro_9",
        "name": "Full Deep Diagnostic & Verified Lead Dossier",
        "price_usd": 9,
        "type": "one_time",
        "features": ["Complete 15-Point Revenue Leak Breakdown", "Full Verified Phone & WhatsApp Contact List", "Custom Video Script & Cold Email Template"]
    },
    "pro_saas": {
        "id": "plan_saas_79",
        "name": "LeakGrader Pro SaaS (Monthly)",
        "price_usd": 79,
        "type": "subscription",
        "features": ["Unlimited Lead Generations", "Unlimited Document RAG & Citations", "3-Agent SEO Content Factory", "24/7 Priority Support"]
    },
    "agency_retainer": {
        "id": "plan_agency_1500",
        "name": "Done-For-You 24/7 AI Closer & CRM Setup",
        "price_usd": 1500,
        "type": "retainer",
        "features": ["Custom AI WhatsApp Closer Bot Setup", "Custom CRM Integration", "Dedicated Server & White-Label Domain", "Ongoing maintenance included"]
    }
}

class PaymentEngine:
    def __init__(self, config_path: str = None):
        self.config_path = config_path or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config", "payment_links.json")
        self.orders = []

    def _get_live_url(self, plan_key: str) -> str:
        # Check environment variables first
        env_map = {
            "micro_audit": os.environ.get("LEMON_URL_MICRO", ""),
            "pro_saas": os.environ.get("LEMON_URL_PRO", ""),
            "agency_retainer": os.environ.get("LEMON_URL_RETAINER", "")
        }
        if env_map.get(plan_key):
            return env_map[plan_key]

        # Check config file
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get(plan_key, {}).get("checkout_url", "")
            except Exception:
                pass
        return ""

    def create_checkout_session(self, plan_key: str, customer_email: str = "client@example.com") -> dict:
        plan = PLANS.get(plan_key, PLANS["micro_audit"])
        order_id = f"ord_{int(time.time()*1000)}"
        live_checkout_url = self._get_live_url(plan_key)

        order = {
            "order_id": order_id,
            "plan_name": plan["name"],
            "amount_usd": plan["price_usd"],
            "customer_email": customer_email,
            "status": "ACTIVE_CHECKOUT" if live_checkout_url else "COMPLETED",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "checkout_url": live_checkout_url or f"/checkout-success?order_id={order_id}&plan={plan_key}",
            "is_live_payment": bool(live_checkout_url),
            "unlock_token": f"tok_{abs(hash(order_id)) % 1000000}"
        }
        self.orders.append(order)
        return order

    def get_order_status(self, order_id: str) -> dict:
        for o in self.orders:
            if o["order_id"] == order_id:
                return o
        return {"error": "Order not found"}
