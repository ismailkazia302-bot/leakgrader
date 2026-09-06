"""
LeakGrader.com - Local Business Outreach & Value Pitch Generator
Stage 5 Engine: Crafts high-converting, personalized cold email copy and 
1-click WhatsApp web pitch links with dynamic pricing (₹50k - ₹1 Lakh).
"""

import urllib.parse
import re

class PitchGenerator:
    def __init__(self, base_url: str = "https://leakgrader.com"):
        self.base_url = base_url

    def generate_pitch(self, business: dict, demo_meta: dict, classification: dict) -> dict:
        """
        Generates personalized cold email and WhatsApp pitch for a business.
        """
        name = (business.get("Business Name") or business.get("name") or "Business Owner").strip()
        phone = (business.get("Phone") or business.get("phone") or "").strip()
        address = (business.get("Address") or business.get("address") or "").strip()
        category = (business.get("Category") or business.get("category") or "Local Business").strip()
        status = business.get("Status", classification.get("Status", "Outdated"))
        
        # Determine city
        city = "your city"
        if address:
            parts = [p.strip() for p in address.split(",") if p.strip()]
            if len(parts) >= 2:
                city = parts[-2]

        demo_id = demo_meta.get("demo_id", "")
        demo_link = f"{self.base_url}/preview/{demo_id}"
        price = demo_meta.get("pitch_price", "₹50,000")

        fail_reasons = classification.get("FailReasons", [])
        if not fail_reasons:
            if status == "No Website":
                issue_summary = "Your business currently has zero verified website on Google Maps, meaning over 70% of potential local clients immediately bounce to competitors."
            else:
                issue_summary = "Your current website lacks mobile optimization and SSL security, causing high visitor drop-off."
        else:
            issue_summary = "Our automated diagnostic detected critical revenue leaks on your current setup: " + "; ".join(fail_reasons[:2]) + "."

        # --- EMAIL COPY ---
        subject = f"Redesign concept for {name} ({city}) — fixing your visitor drop-off"

        email_body = f"""Hi {name} Team,

I was searching for top-rated {category} services in {city} and came across your business profile on Google Maps.

{issue_summary}

According to Google and Harvard Business Review data, local buyers who cannot instantly contact a business on mobile or WhatsApp bounce to a competitor within 60 seconds.

Rather than just sending advice, our team went ahead and pre-built a modern, fast, mobile-first redesign concept specifically tailored for {name}:

👉 View Your Live Redesign Preview: {demo_link}

Key improvements we engineered into your demo:
1. ⚡ Sub-second mobile loading with direct 1-tap WhatsApp and phone appointment booking.
2. 🔒 Full 256-bit SSL certificate security and clean responsive UI.
3. ⭐ Prominent Google review social proof and clear service pricing tiers.

We deploy this entire turnkey system for a flat one-time fee of {price} (no recurring hidden agency fees), designed to pay for itself with just 1 or 2 new bookings.

Would you be open to a quick 5-minute chat this week to review the demo together, or should I send over the deployment checklist?

Best regards,

Growth Engineering Team | LeakGrader
Direct WhatsApp: https://wa.me/919876543210
Website: https://leakgrader.com
"""

        # --- WHATSAPP COPY ---
        wa_phone_clean = re.sub(r'[^0-9]', '', phone)
        wa_text = f"Hi {name}! Saw your {category} on Google in {city}. Noticed your site has high mobile dropoff, so our team pre-built a modern 1-page redesign demo for you here: {demo_link} . We can launch this complete setup for {price}. Would you like to review it?"
        
        wa_link = f"https://wa.me/{wa_phone_clean}?text={urllib.parse.quote(wa_text)}" if wa_phone_clean else ""

        # Mailto link
        mailto_link = f"mailto:?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(email_body)}"

        return {
            "email_subject": subject,
            "email_body": email_body,
            "whatsapp_text": wa_text,
            "whatsapp_link": wa_link,
            "mailto_link": mailto_link,
            "quoted_price": price,
            "demo_link": demo_link
        }
