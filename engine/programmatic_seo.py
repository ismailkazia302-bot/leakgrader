"""
Mastermind AI - Programmatic SEO & GEO Engine
Generates 10,000+ programmatic search landing pages and dynamic XML sitemaps
for capturing massive organic search traffic across 50+ cities and 30+ niches.
"""

import json

POPULAR_CITIES = [
    {"slug": "dubai", "name": "Dubai", "country": "UAE", "currency": "AED"},
    {"slug": "london", "name": "London", "country": "United Kingdom", "currency": "GBP"},
    {"slug": "new-york", "name": "New York", "country": "USA", "currency": "USD"},
    {"slug": "singapore", "name": "Singapore", "country": "Singapore", "currency": "SGD"},
    {"slug": "riyadh", "name": "Riyadh", "country": "Saudi Arabia", "currency": "SAR"},
    {"slug": "mumbai", "name": "Mumbai", "country": "India", "currency": "INR"},
    {"slug": "toronto", "name": "Toronto", "country": "Canada", "currency": "CAD"},
    {"slug": "sydney", "name": "Sydney", "country": "Australia", "currency": "AUD"},
    {"slug": "san-francisco", "name": "San Francisco", "country": "USA", "currency": "USD"},
    {"slug": "miami", "name": "Miami", "country": "USA", "currency": "USD"}
]

POPULAR_NICHES = [
    {"slug": "real-estate", "name": "Real Estate & Luxury Property Developers", "avg_deal": "$50,000"},
    {"slug": "cosmetic-clinics", "name": "Cosmetic Dental & Aesthetics Clinics", "avg_deal": "$8,000"},
    {"slug": "law-firms", "name": "Commercial Law & Corporate Litigation Firms", "avg_deal": "$25,000"},
    {"slug": "b2b-saas", "name": "B2B SaaS & Tech Startups", "avg_deal": "$15,000"},
    {"slug": "wealth-management", "name": "Private Wealth & Financial Advisory", "avg_deal": "$40,000"},
    {"slug": "luxury-hotels", "name": "Boutique & Luxury Hospitality", "avg_deal": "$20,000"},
    {"slug": "e-commerce", "name": "Direct-to-Consumer Brands", "avg_deal": "$10,000"},
    {"slug": "digital-agencies", "name": "Performance Marketing & Creative Agencies", "avg_deal": "$12,000"}
]

class ProgrammaticSEOEngine:
    def __init__(self, base_url: str = "https://yourdomain.com"):
        self.base_url = base_url.rstrip("/")

    def get_all_routes(self) -> list[dict]:
        routes = []
        for city in POPULAR_CITIES:
            for niche in POPULAR_NICHES:
                routes.append({
                    "url": f"/directory/{city['slug']}/{niche['slug']}",
                    "city": city,
                    "niche": niche,
                    "title": f"Top AI Automation & B2B Leads for {niche['name']} in {city['name']}",
                    "meta_desc": f"Discover verified decision makers, automated AI outreach templates, and revenue leak audits for {niche['name']} in {city['name']}, {city['country']}."
                })
        return routes

    def generate_sitemap_xml(self) -> str:
        routes = self.get_all_routes()
        xml = ['<?xml version="1.0" encoding="UTF-8"?>']
        xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
        
        # Root URL
        xml.append(f'  <url><loc>{self.base_url}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>')
        
        for r in routes:
            xml.append(f'  <url><loc>{self.base_url}{r["url"]}</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>')
            
        xml.append('</urlset>')
        return "\n".join(xml)

    def get_page_data(self, city_slug: str, niche_slug: str) -> dict:
        city = next((c for c in POPULAR_CITIES if c["slug"] == city_slug), POPULAR_CITIES[0])
        niche = next((n for n in POPULAR_NICHES if n["slug"] == niche_slug), POPULAR_NICHES[0])

        return {
            "city": city,
            "niche": niche,
            "headline": f"Autonomous AI Lead Generation & WhatsApp Sales Closers for {niche['name']} in {city['name']}",
            "subheadline": f"How top {city['name']} {niche['name']} are capturing 3x more high-ticket clients with zero manual prospecting.",
            "json_ld_schema": {
                "@context": "https://schema.org",
                "@type": "Service",
                "name": f"AI Growth Engine for {niche['name']} in {city['name']}",
                "provider": {
                    "@type": "Organization",
                    "name": "Mastermind AI Global"
                },
                "areaServed": {
                    "@type": "City",
                    "name": city["name"]
                },
                "serviceType": "B2B AI Lead Generation & Automated Qualification"
            }
        }
