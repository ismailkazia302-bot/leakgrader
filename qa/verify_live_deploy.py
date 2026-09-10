report_text = """# Mobile Optimization Audit Report (LeakGrader)

**Date:** 2026-09-09  
**Branch:** `feature/mobile-optimization`  
**Status:** Audit Complete (Read-Only Phase)  

---

## Executive Summary

A comprehensive mobile responsiveness and usability audit was performed across all 9 HTML documents and the global stylesheet (`web/style.css`) in the LeakGrader web platform:
- `web/index.html` (Main Autonomous Scanner & Product Suite)
- `web/about.html` (Company & Mission)
- `web/contact.html` (Enterprise Inquiries & Support)
- `web/privacy.html` (Privacy Policy)
- `web/terms.html` (Terms of Service)
- `web/login.html` (Authentication)
- `web/signup.html` (Onboarding)
- `web/dashboard.html` (User Dashboard & Audit History)
- `web/account.html` (Account & Workspace Settings)
- `web/style.css` (Global Design System & Layout Tokens)

---

## Prioritized Bug Matrix by Severity

| Severity | Count | Primary Impact Areas |
|---|---|---|
| **CRITICAL** | 3 | Broken table on mobile (`dashboard.html`), completely hidden navigation with no mobile menu (`about.html`), iOS viewport auto-zooming on 13px/14px inputs (`contact.html`, `login.html`, `signup.html`, `account.html`, `index.html`). |
| **HIGH** | 5 | Sub-44px touch targets on buttons & chips, unscrollable tables, lack of mobile hamburger navigation, non-responsive 2-column info grids on mobile (`account.html`), cramped card padding on small screens (<375px). |
| **MEDIUM** | 5 | Fixed font sizes instead of fluid `clamp()`, missing `max-width: 100%` and `overflow-x: hidden` on standalone pages, missing mobile breakpoints (320px, 375px, 390px), newsletter input `min-width: 240px` on mobile. |
| **LOW** | 3 | Missing `<meta name="theme-color">` on 8 pages, missing `<meta name="description">` on 6 pages, non-deferred external scripts. |
| **TOTAL** | **16** | **All 16 issues scheduled for systematic resolution in Phase 2.** |

---

## Detailed Audit Breakdown Across 12 Criteria

### 1. Viewport Meta Tag
- **Findings:** Present in all 9 HTML files: `<meta name="viewport" content="width=device-width, initial-scale=1.0">` (with `viewport-fit=cover` on marketing pages).
- **Severity:** `CLEAN` (No defects).

### 2. Horizontal Scrolling & Overflow
- **Findings:**
  - `web/style.css` declares `overflow-x: hidden` on `html, body`.
  - However, standalone pages (`dashboard.html`, `account.html`, `login.html`, `signup.html`, `privacy.html`, `terms.html`) use internal stylesheets that omit `max-width: 100%` and `overflow-x: hidden`.
  - In `dashboard.html`, `<table id="auditsTable">` (5 columns) lacks an overflow wrapper (`overflow-x: auto`), causing horizontal table blowout on viewport widths < 600px.
- **Severity:** `CRITICAL` (FIX-02, FIX-14).

### 3. Typography & Font Sizing
- **Findings:**
  - Base body font in `style.css` is `13px`, below the 14px mobile readability baseline.
  - Inputs across `contact.html`, `login.html`, `signup.html`, and `account.html` use `font-size: 14px;` (and `13px` in `style.css` mobile input bar). On iOS Safari, any input font smaller than `16px` forces an automatic viewport zoom that disrupts layout.
  - Headings in `about.html` (`52px`), `privacy.html` (`36px`), and `terms.html` (`36px`) use fixed sizes rather than `clamp()`.
- **Severity:** `CRITICAL` (FIX-03, FIX-07).

### 4. Touch Targets
- **Findings:**
  - In `index.html`: `.chip-sample` (`padding: 4px 10px; font-size: 11px;`) has an effective height of ~22px (< 44px).
  - In `index.html`: `.metric-preset-chip` has `padding: 2px 8px; font-size: 10.5px;` (~18px height).
  - In `index.html`: `.btn-upgrade-3d` has `padding: 4px 7px !important;` on small screens (< 30px height).
  - In `dashboard.html`: `.btn-sm` has `padding: 8px 14px;` (< 44px).
  - In `about.html`: `.btn-cta-nav` has `padding: 8px 16px;` (< 44px).
- **Severity:** `HIGH` (FIX-05).

### 5. Navigation & Mobile Menus
- **Findings:**
  - `index.html` has a bottom rail on mobile for primary tabs, but topbar utility links (About, Pricing, Contact, Log In, Sign Up) lack a cohesive mobile drawer/dropdown.
  - `about.html` sets `@media (max-width: 768px) { .nav-links { display: none; } }`, completely hiding navigation without providing a hamburger toggle or mobile drawer.
  - `contact.html`, `dashboard.html`, `account.html` lack mobile-friendly responsive navigation menus.
- **Severity:** `CRITICAL` (FIX-04).

### 6. Images and Media
- **Findings:**
  - Inline SVGs and logo marks do not have explicit `max-width: 100%` and `height: auto` protection against container overflow.
- **Severity:** `MEDIUM` (FIX-06).

### 7. Form Usability
- **Findings:**
  - `contact.html`: Form inputs use `font-size: 14px`, lacking full 44px minimum tap height and 48px submit button height.
  - `login.html` & `signup.html`: Inputs use `14px` font size and `.auth-card` padding is `36px 32px;` which is cramped on 320px-375px screens.
  - `index.html`: Newsletter email input has `min-width: 240px;` and lacks full-width stacking below 640px.
- **Severity:** `HIGH` (FIX-07, FIX-13).

### 8. Flexbox & Grid Stacking
- **Findings:**
  - `account.html`: `.info-grid` is hardcoded to `grid-template-columns: 140px 1fr;` without mobile media query, crushing account values on 320px/375px screens.
  - `dashboard.html`: `.grid-stats` does not collapse gracefully to 1fr on narrow viewports.
  - `contact.html`: `.form-row` has 640px query but requires clean 768px stacking.
- **Severity:** `HIGH` (FIX-08).

### 9. Spacing & Lateral Padding
- **Findings:**
  - `dashboard.html`: `header` has `padding: 16px 32px;` and `main` has `padding: 0 24px;`. Needs 16px lateral padding on mobile.
  - `login.html` & `signup.html`: `body { padding: 24px; }` causes cards on 320px screens to overflow. Needs `16px` on mobile.
  - `privacy.html` & `terms.html`: `.legal-container` has `padding: 48px 24px 80px;`. Needs `24px 16px 48px;` on mobile.
- **Severity:** `MEDIUM` (FIX-09).

### 10. Homepage Specific Elements
- **Findings:**
  - Hero headline needs fluid `clamp(24px, 6vw, 40px)`.
  - Custom revenue metrics accordion (`#custom-metrics-panel`) has inputs with 13px font and preset chips under 20px height.
  - The audit input bar needs full width and 48px submit button on mobile.
- **Severity:** `HIGH` (FIX-10, FIX-11).

### 11. CSS Breakpoints Defined
- **Findings:**
  - `style.css` currently uses `1024px`, `768px`, and `380px`.
  - Missing standardized breakpoints: `320px` (small phone), `375px` (iPhone SE/standard), `390px` (modern iPhone), `414px` (iPhone Plus), `768px` (tablet), `1024px` (desktop), `1440px` (large desktop).
- **Severity:** `MEDIUM`.

### 12. Mobile Performance Quick Wins
- **Findings:**
  - 8 pages lack `<meta name="theme-color" content="#06080e">`.
  - 6 pages lack `<meta name="description">` tags.
  - External script tags in `about.html` and `dashboard.html` can leverage `defer`.
- **Severity:** `LOW` (Phase 4).

---

## Action Plan for Phase 2 Execution

1. Apply **FIX-01 through FIX-14** systematically.
2. Ensure mobile-first styling and fluid typography (`clamp`).
3. Add full-width touch-friendly inputs with `font-size: 16px` to eradicate iOS zoom.
4. Implement responsive hamburger navigation across pages.
5. Wrap data tables with horizontal touch scrolling.
"""

with open('qa/MOBILE_AUDIT_2026-09-09.md', 'w', encoding='utf-8') as f:
    f.write(report_text)

print("MOBILE_AUDIT_2026-09-09.md successfully generated!")

for fn in files:
    with open(os.path.join(web_dir, fn), 'r', encoding='utf-8') as f:
        html = f.read()
    tc = re.search(r'<meta[^>]+name=[\"\']theme-color[\"\'][^>]*>', html, re.I)
    desc = re.search(r'<meta[^>]+name=[\"\']description[\"\'][^>]*>', html, re.I)
    title = re.search(r'<title>([^<]+)</title>', html, re.I)
    report['meta'][fn] = {
        'theme_color': tc.group(0) if tc else 'MISSING',
        'description': desc.group(0) if desc else 'MISSING',
        'title': title.group(1).strip() if title else 'MISSING'
    }

# 3. Navigation / Hamburger
report['nav'] = {}
for fn in files:
    with open(os.path.join(web_dir, fn), 'r', encoding='utf-8') as f:
        html = f.read()
    has_nav = '<nav' in html.lower()
    has_header = '<header' in html.lower()
    has_burger = any(x in html.lower() for x in ['hamburger', 'menu-toggle', 'mobile-menu', 'nav-toggle', 'navbar-toggler'])
    report['nav'][fn] = {
        'has_nav': has_nav,
        'has_header': has_header,
        'has_burger': has_burger
    }

# 4. Tables without scroll wrappers
report['tables'] = {}
for fn in files:
    with open(os.path.join(web_dir, fn), 'r', encoding='utf-8') as f:
        html = f.read()
    tables = re.findall(r'<table[^>]*>', html, re.I)
    has_scroll = 'overflow-x: auto' in html or 'overflow:auto' in html or 'table-scroll-wrapper' in html
    report['tables'][fn] = {
        'table_count': len(tables),
        'has_scroll_wrapper': has_scroll
    }

# 5. Media queries in CSS and HTML
report['media_queries'] = {}
medias_css = re.findall(r'@media[^{]+', css)
report['media_queries']['web/style.css'] = sorted(set(m.strip() for m in medias_css))
for fn in files:
    with open(os.path.join(web_dir, fn), 'r', encoding='utf-8') as f:
        html = f.read()
    h_medias = re.findall(r'@media[^{]+', html)
    if h_medias:
        report['media_queries'][fn] = sorted(set(m.strip() for m in h_medias))

print(json.dumps(report, indent=2))
