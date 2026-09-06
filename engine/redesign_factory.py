"""
LeakGrader.com - Local Business Redesign Generator Factory
Stage 4 Engine: Auto-generates premium, conversion-optimized one-page website concepts
for businesses with No Website or Outdated sites.
Embeds non-intrusive watermarking and stores live preview demos in storage/demos/.
"""

import os
import json
import time
import re

NICHE_THEMES = {
    "dental": {
        "tagline": "Painless, State-of-the-Art Dental Care & Smile Transformations",
        "primary_color": "#0ea5e9",
        "accent_color": "#0284c7",
        "services": [
            {"title": "Invisible Aligners & Orthodontics", "desc": "Custom digital aligners with 3D scan visualization.", "price": "From ₹45,000"},
            {"title": "Single-Visit Root Canal Treatment", "desc": "Painless laser-assisted therapy with digital precision.", "price": "From ₹6,500"},
            {"title": "Cosmetic Smile Makeover & Veneers", "desc": "Ultra-thin porcelain veneers handcrafted for natural beauty.", "price": "From ₹15,000"},
            {"title": "Titanium Dental Implants", "desc": "Lifetime warranted restorative implants by senior surgeons.", "price": "From ₹25,000"}
        ]
    },
    "real estate": {
        "tagline": "Exclusive Luxury Properties, Penthouses & Prime Investment Portfolios",
        "primary_color": "#d97706",
        "accent_color": "#b45309",
        "services": [
            {"title": "Prime Residential Acquisitions", "desc": "Handpicked luxury villas, sea-facing residences, and penthouses.", "price": "Consultation Free"},
            {"title": "High-Yield Commercial Assets", "desc": "Grade-A pre-leased office spaces delivering 8-10% rental yields.", "price": "Verified Deals"},
            {"title": "Off-Plan & Pre-Launch Portfolios", "desc": "Direct developer allocations with flexible structured payment plans.", "price": "Zero Brokerage"},
            {"title": "Property Asset Management", "desc": "Turnkey tenant screening, lease legalities, and automated rent collection.", "price": "Full Service"}
        ]
    },
    "salon": {
        "tagline": "Luxury Hair Styling, Skin Aesthetics & Holistic Rejuvenation",
        "primary_color": "#ec4899",
        "accent_color": "#db2777",
        "services": [
            {"title": "Couture Haircuts & Master Color", "desc": "Balayage, keratin smoothing, and bespoke precision cuts.", "price": "From ₹2,500"},
            {"title": "HydraFacial & Medical Aesthetics", "desc": "Deep pore extraction, peptide infusion, and radiant skin glow.", "price": "From ₹4,500"},
            {"title": "Bridal & Red Carpet Glamour", "desc": "Complete HD makeup, hairstyling, and couture draping.", "price": "From ₹18,000"},
            {"title": "Aroma Stress-Relief Spa", "desc": "Botanical deep-tissue relaxation by certified therapists.", "price": "From ₹3,500"}
        ]
    },
    "legal": {
        "tagline": "Aggressive Corporate Defense, High-Stakes Litigation & Strategic Counsel",
        "primary_color": "#6366f1",
        "accent_color": "#4f46e5",
        "services": [
            {"title": "Commercial Litigation & Arbitration", "desc": "Strategic representation across High Courts, NCLT, and dispute tribunals.", "price": "Retainer Available"},
            {"title": "Mergers, Acquisitions & Contracts", "desc": "Ironclad contract drafting, due diligence, and regulatory compliance.", "price": "Corporate Advisory"},
            {"title": "Real Estate & Title Due Diligence", "desc": "30-year property title verification and municipal clearance checks.", "price": "Fixed Fee"},
            {"title": "Intellectual Property & Trademark", "desc": "Global patent filing, brand trademark defense, and copyright enforcement.", "price": "From ₹12,000"}
        ]
    },
    "default": {
        "tagline": "Premium Professional Solutions Delivered with Guaranteed Excellence",
        "primary_color": "#38bdf8",
        "accent_color": "#0055ff",
        "services": [
            {"title": "Comprehensive Consultation & Audit", "desc": "Thorough in-person or virtual diagnostic assessment of your exact requirements.", "price": "Direct Quote"},
            {"title": "Turnkey Implementation & Service", "desc": "Executed by senior certified technicians with strict quality assurance.", "price": "Guaranteed Results"},
            {"title": "Priority Same-Day Dispatch", "desc": "Emergency fast-track turnaround available across your local city.", "price": "Rapid Support"},
            {"title": "Annual Maintenance & Support", "desc": "Continuous monitoring, scheduled checkups, and dedicated account manager.", "price": "Custom Retainer"}
        ]
    }
}

class RedesignFactory:
    def __init__(self, storage_dir: str = None):
        self.storage_dir = storage_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "storage")
        self.demos_dir = os.path.join(self.storage_dir, "demos")
        os.makedirs(self.demos_dir, exist_ok=True)

    def generate_redesign(self, business: dict) -> dict:
        """
        Creates a complete, watermarked HTML/CSS redesign demo tailored to the business.
        Saves file in storage/demos/{demo_id}.html and returns demo metadata.
        """
        name = (business.get("Business Name") or business.get("name") or "Your Business").strip()
        phone = (business.get("Phone") or business.get("phone") or "").strip()
        address = (business.get("Address") or business.get("address") or "").strip()
        category = (business.get("Category") or business.get("category") or "Services").strip()
        website = (business.get("Website") or business.get("website") or "").strip()
        status = business.get("Status", "Outdated")

        # Determine City
        city = "Your City"
        for part in address.split(","):
            part_clean = part.strip()
            if any(c in part_clean.lower() for c in ["mumbai", "delhi", "bangalore", "bengaluru", "hyderabad", "chennai", "kolkata", "pune", "dubai", "london", "new york", "ahmedabad", "gurgaon", "noida"]):
                city = part_clean
                break
        if city == "Your City" and address:
            parts = [p.strip() for p in address.split(",") if p.strip()]
            if len(parts) >= 2:
                city = parts[-2]

        # Determine Niche Theme
        cat_lower = category.lower()
        theme_key = "default"
        for k in NICHE_THEMES:
            if k in cat_lower:
                theme_key = k
                break
        theme = NICHE_THEMES[theme_key]

        demo_id = f"demo_{abs(hash(name + phone + city)) % 1000000:06d}"
        demo_url = f"/preview/{demo_id}"

        # Pricing Tier
        is_high_ticket = any(k in cat_lower for k in ["dental", "real estate", "law", "legal", "clinic", "hospital", "architect", "plastic"])
        pitch_price = "₹1,00,000" if is_high_ticket else "₹50,000"

        # Build Full HTML Content
        html_code = self._build_html(
            demo_id=demo_id,
            name=name,
            phone=phone,
            address=address,
            city=city,
            category=category,
            website=website,
            status=status,
            theme=theme,
            pitch_price=pitch_price
        )

        # Save Demo File
        demo_file = os.path.join(self.demos_dir, f"{demo_id}.html")
        with open(demo_file, "w", encoding="utf-8") as f:
            f.write(html_code)

        return {
            "demo_id": demo_id,
            "demo_url": demo_url,
            "demo_file": demo_file,
            "pitch_price": pitch_price,
            "preview_link": f"https://leakgrader.com{demo_url}"
        }

    def _build_html(self, demo_id, name, phone, address, city, category, website, status, theme, pitch_price) -> str:
        services_cards = "".join([
            f"""
            <div class="svc-card">
              <div class="svc-icon"><i data-lucide="check-circle-2"></i></div>
              <h3>{s['title']}</h3>
              <p>{s['desc']}</p>
              <div class="svc-footer">
                <span class="svc-price">{s['price']}</span>
                <a href="#book" class="svc-btn">Book Now ➔</a>
              </div>
            </div>
            """ for s in theme["services"]
        ])

        wa_clean_phone = re.sub(r'[^0-9]', '', phone)
        wa_link = f"https://wa.me/{wa_clean_phone}?text=Hi%20{name}%2C%20I%20saw%20your%20services%20online" if wa_clean_phone else "#book"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{name} — Official Redesign Concept | {city}</title>
  <meta name="description" content="Official modern concept for {name} ({category} in {city}). Fast mobile loading, direct WhatsApp booking, and verified credentials.">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@600;800&display=swap" rel="stylesheet">
  <script src="https://unpkg.com/lucide@latest"></script>

  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --primary: {theme['primary_color']};
      --accent: {theme['accent_color']};
      --bg: #090b10;
      --card-bg: rgba(18, 22, 34, 0.85);
      --border: rgba(255, 255, 255, 0.08);
      --text: #f8fafc;
      --text-muted: #94a3b8;
    }}
    body {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.6;
      padding-top: 56px; /* Space for watermark bar */
      padding-bottom: 70px;
    }}

    /* 🏷️ WATERMARK TOP BANNER */
    .leakgrader-watermark-top {{
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      z-index: 999999;
      background: linear-gradient(90deg, #0b0f19, #0284c7, #0b0f19);
      color: #ffffff;
      padding: 10px 18px;
      font-size: 12px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid rgba(56, 189, 248, 0.4);
      box-shadow: 0 4px 20px rgba(0,0,0,0.8);
      font-weight: 700;
    }}
    .watermark-pill {{
      background: rgba(0, 0, 0, 0.5);
      border: 1px solid rgba(255,255,255,0.2);
      padding: 4px 10px;
      border-radius: 9999px;
      font-size: 11px;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }}
    .watermark-claim-btn {{
      background: #ffffff;
      color: #0b0f19;
      border: none;
      padding: 6px 14px;
      border-radius: 6px;
      font-weight: 800;
      font-size: 11px;
      text-decoration: none;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: transform 0.15s;
    }}
    .watermark-claim-btn:hover {{ transform: scale(1.03); }}

    /* MAIN CONTAINER */
    .container {{
      max-width: 1140px;
      margin: 0 auto;
      padding: 0 20px;
    }}

    /* HEADER */
    header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 24px 0;
      border-bottom: 1px solid var(--border);
    }}
    .brand-box h1 {{
      font-size: 22px;
      font-weight: 900;
      color: #ffffff;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .brand-category {{
      font-size: 12px;
      color: var(--primary);
      text-transform: uppercase;
      font-weight: 800;
      letter-spacing: 0.05em;
    }}
    .nav-cta-group {{
      display: flex;
      gap: 12px;
      align-items: center;
    }}
    .btn-call-header {{
      background: rgba(255,255,255,0.06);
      border: 1px solid var(--border);
      color: #ffffff;
      text-decoration: none;
      padding: 8px 16px;
      border-radius: 8px;
      font-weight: 700;
      font-size: 13px;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }}
    .btn-book-header {{
      background: var(--primary);
      color: #000;
      text-decoration: none;
      padding: 8px 18px;
      border-radius: 8px;
      font-weight: 800;
      font-size: 13px;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }}

    /* HERO */
    .hero {{
      padding: 60px 0 40px;
      text-align: center;
    }}
    .hero-badge {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: rgba(56, 189, 248, 0.1);
      border: 1px solid rgba(56, 189, 248, 0.3);
      padding: 6px 14px;
      border-radius: 9999px;
      color: var(--primary);
      font-size: 12px;
      font-weight: 800;
      margin-bottom: 20px;
    }}
    .hero-title {{
      font-size: clamp(32px, 5vw, 54px);
      font-weight: 900;
      line-height: 1.15;
      margin-bottom: 18px;
      color: #ffffff;
    }}
    .hero-title span {{
      color: var(--primary);
    }}
    .hero-sub {{
      font-size: 18px;
      color: var(--text-muted);
      max-width: 680px;
      margin: 0 auto 30px;
      line-height: 1.6;
    }}
    .hero-actions {{
      display: flex;
      justify-content: center;
      gap: 14px;
      flex-wrap: wrap;
    }}
    .btn-wa-hero {{
      background: #25D366;
      color: #ffffff;
      padding: 14px 28px;
      border-radius: 10px;
      font-weight: 800;
      font-size: 15px;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      box-shadow: 0 10px 30px rgba(37, 211, 102, 0.3);
    }}
    .btn-call-hero {{
      background: rgba(255,255,255,0.06);
      border: 1px solid rgba(255,255,255,0.15);
      color: #ffffff;
      padding: 14px 26px;
      border-radius: 10px;
      font-weight: 700;
      font-size: 15px;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 8px;
    }}

    /* TRUST PROOF STRIP */
    .proof-strip {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
      margin: 40px 0 60px;
    }}
    .proof-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 18px 20px;
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .proof-icon {{
      width: 40px;
      height: 40px;
      border-radius: 10px;
      background: rgba(56, 189, 248, 0.12);
      color: var(--primary);
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }}
    .proof-title {{ font-size: 14px; font-weight: 800; color: #ffffff; }}
    .proof-desc {{ font-size: 11.5px; color: var(--text-muted); }}

    /* SERVICES GRID */
    .section-head {{
      text-align: center;
      margin-bottom: 36px;
    }}
    .section-head h2 {{
      font-size: 30px;
      font-weight: 800;
      color: #ffffff;
      margin-bottom: 8px;
    }}
    .section-head p {{ font-size: 15px; color: var(--text-muted); }}

    .svc-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 20px;
      margin-bottom: 60px;
    }}
    .svc-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 26px 22px;
      display: flex;
      flex-direction: column;
      gap: 12px;
      transition: transform 0.2s, border-color 0.2s;
    }}
    .svc-card:hover {{
      transform: translateY(-4px);
      border-color: rgba(56, 189, 248, 0.4);
    }}
    .svc-icon {{
      width: 36px;
      height: 36px;
      border-radius: 8px;
      background: rgba(56, 189, 248, 0.15);
      color: var(--primary);
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    .svc-card h3 {{ font-size: 18px; font-weight: 800; color: #ffffff; }}
    .svc-card p {{ font-size: 13.5px; color: var(--text-muted); line-height: 1.5; }}
    .svc-footer {{
      margin-top: auto;
      padding-top: 14px;
      border-top: 1px solid var(--border);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .svc-price {{ font-size: 12px; font-weight: 800; color: #10b981; font-family:'JetBrains Mono', monospace; }}
    .svc-btn {{ font-size: 12px; color: var(--primary); font-weight: 700; text-decoration: none; }}

    /* FAST BOOKING SECTION */
    .booking-section {{
      background: linear-gradient(180deg, rgba(18, 24, 38, 0.95), rgba(10, 13, 20, 0.95));
      border: 1px solid rgba(56, 189, 248, 0.3);
      border-radius: 18px;
      padding: 40px;
      margin-bottom: 60px;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 36px;
      align-items: center;
    }}
    .booking-info h2 {{ font-size: 28px; font-weight: 800; color: #ffffff; margin-bottom: 12px; }}
    .booking-info p {{ font-size: 14.5px; color: var(--text-muted); margin-bottom: 20px; }}
    .contact-item {{
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 12px;
      font-size: 14px;
      color: #cbd5e1;
    }}
    .booking-form {{
      display: flex;
      flex-direction: column;
      gap: 12px;
      background: rgba(0,0,0,0.3);
      padding: 24px;
      border-radius: 12px;
      border: 1px solid var(--border);
    }}
    .booking-form input, .booking-form select {{
      width: 100%;
      background: #0d111a;
      border: 1px solid rgba(255,255,255,0.12);
      border-radius: 8px;
      padding: 12px 14px;
      color: #ffffff;
      font-size: 13.5px;
      outline: none;
    }}
    .btn-submit-booking {{
      background: linear-gradient(135deg, var(--primary), var(--accent));
      color: #fff;
      border: none;
      padding: 13px;
      border-radius: 8px;
      font-weight: 800;
      font-size: 14px;
      cursor: pointer;
    }}

    /* FOOTER */
    footer {{
      border-top: 1px solid var(--border);
      padding: 24px 0;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
      font-size: 12px;
      color: var(--text-muted);
    }}

    @media (max-width: 768px) {{
      .booking-section {{ grid-template-columns: 1fr; padding: 24px 18px; }}
      .leakgrader-watermark-top {{ flex-direction: column; gap: 6px; text-align: center; }}
      body {{ padding-top: 76px; }}
    }}
  </style>
</head>
<body>

  <!-- 🏷️ WATERMARK TOP BAR -->
  <div class="leakgrader-watermark-top">
    <div style="display:flex; align-items:center; gap:8px;">
      <span class="watermark-pill">
        <i data-lucide="sparkles" style="width:12px; height:12px; color:#38bdf8;"></i>
        PROPOSED REDESIGN DEMO FOR {name.upper()}
      </span>
      <span style="color:#cbd5e1; font-size:11px;">Current Status: <strong style="color:#fbbf24;">{status}</strong></span>
    </div>
    <div style="display:flex; align-items:center; gap:10px;">
      <span style="font-size:11px; color:#94a3b8;">Full Build Price: <strong style="color:#10b981;">{pitch_price}</strong></span>
      <a href="https://leakgrader.com/contact?subject=Redesign%20Claim%20for%20{re.sub(r'[^a-zA-Z0-9]', '%20', name)}" target="_blank" class="watermark-claim-btn">
        <span>Claim & Launch This Site ➔</span>
      </a>
    </div>
  </div>

  <div class="container">
    
    <!-- HEADER -->
    <header>
      <div class="brand-box">
        <h1>
          <i data-lucide="building-2" style="color:var(--primary);"></i>
          <span>{name}</span>
        </h1>
        <div class="brand-category">{category} • {city}</div>
      </div>

      <div class="nav-cta-group">
        <a href="tel:{phone}" class="btn-call-header">
          <i data-lucide="phone" style="width:14px; height:14px; color:var(--primary);"></i>
          <span>{phone or 'Call Direct'}</span>
        </a>
        <a href="#book" class="btn-book-header">
          <i data-lucide="calendar" style="width:14px; height:14px;"></i>
          <span>Book Appointment</span>
        </a>
      </div>
    </header>

    <!-- HERO -->
    <section class="hero">
      <div class="hero-badge">
        <i data-lucide="check-circle" style="width:14px; height:14px;"></i>
        VERIFIED {category.upper()} IN {city.upper()}
      </div>
      <h2 class="hero-title">
        Experience Superior {category} in <span>{city}</span>
      </h2>
      <p class="hero-sub">
        {theme['tagline']}. Serving thousands of satisfied local clients with 5-star precision and immediate response.
      </p>

      <div class="hero-actions">
        <a href="{wa_link}" target="_blank" class="btn-wa-hero">
          <i data-lucide="message-circle" style="width:18px; height:18px;"></i>
          <span>Chat on WhatsApp</span>
        </a>
        <a href="tel:{phone}" class="btn-call-hero">
          <i data-lucide="phone" style="width:18px; height:18px;"></i>
          <span>Call: {phone or 'Inquire Now'}</span>
        </a>
      </div>
    </section>

    <!-- PROOF STRIP -->
    <div class="proof-strip">
      <div class="proof-card">
        <div class="proof-icon"><i data-lucide="star"></i></div>
        <div>
          <div class="proof-title">4.9 / 5.0 Star Rating</div>
          <div class="proof-desc">Over 250+ verified local Google reviews</div>
        </div>
      </div>

      <div class="proof-card">
        <div class="proof-icon"><i data-lucide="zap"></i></div>
        <div>
          <div class="proof-title">Immediate Response</div>
          <div class="proof-desc">Direct phone & WhatsApp bookings 24/7</div>
        </div>
      </div>

      <div class="proof-card">
        <div class="proof-icon"><i data-lucide="shield-check"></i></div>
        <div>
          <div class="proof-title">100% Guaranteed Care</div>
          <div class="proof-desc">Senior certified professionals only</div>
        </div>
      </div>
    </div>

    <!-- SERVICES -->
    <section>
      <div class="section-head">
        <h2>Our Core Services & Treatments</h2>
        <p>Transparent pricing, state-of-the-art procedures, and customized solutions.</p>
      </div>

      <div class="svc-grid">
        {services_cards}
      </div>
    </section>

    <!-- BOOKING SECTION -->
    <section class="booking-section" id="book">
      <div class="booking-info">
        <h2>Book Your Appointment in {city}</h2>
        <p>Leave your details below or connect immediately via WhatsApp. Our front desk responds within 5 minutes.</p>

        <div class="contact-item">
          <i data-lucide="map-pin" style="color:var(--primary);"></i>
          <span>{address or city}</span>
        </div>

        <div class="contact-item">
          <i data-lucide="phone" style="color:var(--primary);"></i>
          <span>{phone or 'Available on WhatsApp'}</span>
        </div>

        <div class="contact-item">
          <i data-lucide="clock" style="color:var(--primary);"></i>
          <span>Mon – Sat: 9:00 AM – 8:00 PM</span>
        </div>
      </div>

      <form class="booking-form" onsubmit="event.preventDefault(); alert('Demo preview: Appointment booking simulated successfully!');">
        <input type="text" placeholder="Your Full Name" required>
        <input type="tel" placeholder="Mobile / WhatsApp Number" required>
        <select required>
          <option value="">Select Service Required...</option>
          <option value="1">{theme['services'][0]['title']}</option>
          <option value="2">{theme['services'][1]['title']}</option>
          <option value="3">{theme['services'][2]['title']}</option>
          <option value="4">{theme['services'][3]['title']}</option>
        </select>
        <button type="submit" class="btn-submit-booking">Confirm Priority Booking ➔</button>
      </form>
    </section>

    <!-- FOOTER -->
    <footer>
      <div>
        <span>© 2026 {name}. All rights reserved. • {city}</span>
      </div>
      <div>
        <span>Demo Redesign Engineered by <a href="https://leakgrader.com" style="color:var(--primary); text-decoration:none; font-weight:700;">LeakGrader.com</a></span>
      </div>
    </footer>

  </div>

  <script>
    if (window.lucide) lucide.createIcons();
  </script>
</body>
</html>
"""
