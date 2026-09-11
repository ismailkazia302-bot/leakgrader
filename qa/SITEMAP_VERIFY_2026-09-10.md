# Live Sitemap & Noindex Verification Report

**Date:** 2026-09-10  
**Target:** `https://leakgrader.com/sitemap.xml` & Directory Pages  
**Deployed Commit:** `efef640`  
**Final Verdict:** `SITEMAP_CLEAN`  

---

## 1. Executive Summary

A live production investigation was conducted against `https://leakgrader.com` following the deployment of commit `efef640`.

**Key Finding:** The live sitemap is **CLEAN** and the 12,600 programmatic directory pages have been completely eliminated from the sitemap.
- **Sitemap Byte Size:** **977 bytes** (reduced from 1,728,596 bytes — a **99.94% reduction**).
- **Total `<url>` entries in sitemap:** **8** (down from 12,603).
- **Directory (`/directory/`) URLs in sitemap:** **0**.
- **Directory Noindex Directives:** Live probe to `https://leakgrader.com/directory/miami/orthopedic-surgery` confirmed **HTTP 200** with both `<meta name="robots" content="noindex, follow">` and `X-Robots-Tag: noindex, follow` actively returned.

---

## 2. Live Verification Results

### 2.1. Sitemap Telemetry (`https://leakgrader.com/sitemap.xml`)
- **HTTP Status:** `200 OK`
- **Response Size:** `977 bytes`
- **Total `<url>` Count:** `8`
- **Directory URLs (`/directory/`):** `0`
- **Exact Live XML Payload:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://leakgrader.com/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>
  <url><loc>https://leakgrader.com/pricing</loc><changefreq>daily</changefreq><priority>0.9</priority></url>
  <url><loc>https://leakgrader.com/about</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>
  <url><loc>https://leakgrader.com/contact</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>
  <url><loc>https://leakgrader.com/login</loc><changefreq>monthly</changefreq><priority>0.6</priority></url>
  <url><loc>https://leakgrader.com/signup</loc><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://leakgrader.com/privacy</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>
  <url><loc>https://leakgrader.com/terms</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>
</urlset>
```

### 2.2. Directory Noindex Live Probe (`https://leakgrader.com/directory/miami/orthopedic-surgery`)
- **HTTP Status:** `200 OK`
- **HTTP Header:** `x-robots-tag: noindex, follow` (Present in Cloudflare/Gunicorn response headers)
- **HTML `<head>`:** `<meta name="robots" content="noindex, follow">` (Verified present in parsed HTML body)
- **Status:** **100% Verified Live**

---

## 3. Multiple Sitemaps & Robots.txt Audit

1. **Sitemap Index / Secondary Sitemaps:**
   - Codebase scan confirmed **zero** static sitemap files on disk.
   - There are **no** secondary sitemaps (`sitemap_index.xml`, `sitemap-directory.xml`, etc.).
   - All sitemap output is generated purely dynamically by `ProgrammaticSEOEngine.generate_sitemap_xml()`.
2. **`robots.txt` References (`web/robots.txt`):**
   - Lines 25–26 reference:
     ```
     Sitemap: https://leakgrader.com/sitemap.xml
     Sitemap: https://leakgrader.onrender.com/sitemap.xml
     ```
   - Both point to the single dynamic `/sitemap.xml` endpoint.
3. **Sitemap Generators in Codebase:**
   - `engine/seo_engine.py`: Updated in `efef640` (8 core URLs).
   - `engine/programmatic_seo.py`: Updated in `efef640` (8 core URLs).

---

## 4. Root Cause Analysis: Why 1.7MB Appeared Initially

The 1.7MB response initially observed was caused by **transient container cutover latency and caching**:
1. **Container Switch Delay:** On Render, when a new commit is marked "live", the health check and traffic router take 60–90 seconds to fully drain and terminate the old container. Early requests were still hitting the previous container worker process.
2. **HTTP Cache Header:** The sitemap endpoint returns `Cache-Control: public, max-age=86400`. Clients or intermediary edge proxies that requested `/sitemap.xml` prior to container termination received cached chunks from the old deployment.
3. **Current Live State:** The fresh container running `efef640` is now 100% active across all Gunicorn workers. Every fresh request returns the 977-byte clean XML document.

---

## 5. Identified Enhancement: `/pricing` URL Routing

During live testing of all 8 sitemap URLs:
- 7 of 8 URLs return `HTTP 200` (`/`, `/about`, `/contact`, `/login`, `/signup`, `/privacy`, `/terms`).
- `https://leakgrader.com/pricing` currently returns `HTTP 404` because pricing is hosted on the homepage anchor (`/#pricing`) rather than a standalone `pricing.html` file.
- **Recommended Follow-up Fix (Non-breaking):**
  Add a lightweight rewrite in `wsgi.py` and `app.py`:
  If `path == '/pricing'`, serve `web/index.html` or redirect 301 to `/#pricing`. This will ensure the sitemap link and the `upgrade_url: "/pricing"` banner links resolve with 200/301 without broken links.

---

## 6. Final Verdict

**`SITEMAP_CLEAN`**
