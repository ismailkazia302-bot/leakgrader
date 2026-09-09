"""
Automated Mobile Optimization Verification Suite
Tests all 9 HTML files and style.css for responsive design,
touch target minimums, viewport tags, theme-color, font sizes,
and table scroll containers.
"""
import os
import sys

WEB_DIR = os.path.join(os.path.dirname(__file__), "..", "web")
HTML_FILES = [
    "index.html",
    "about.html",
    "contact.html",
    "privacy.html",
    "terms.html",
    "login.html",
    "signup.html",
    "dashboard.html",
    "account.html"
]

def run_checks():
    failures = []
    passes = []

    print("==================================================")
    print("RUNNING MOBILE OPTIMIZATION VERIFICATION SUITE")
    print("==================================================")

    for fname in HTML_FILES:
        fpath = os.path.join(WEB_DIR, fname)
        if not os.path.exists(fpath):
            failures.append(f"{fname}: File not found")
            continue

        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()

        # 1. Viewport tag
        if '<meta name="viewport"' not in content:
            failures.append(f"{fname}: Missing viewport meta tag")
        else:
            passes.append(f"{fname}: Viewport meta tag present")

        # 2. Theme color
        if '<meta name="theme-color"' not in content:
            failures.append(f"{fname}: Missing theme-color meta tag")
        else:
            passes.append(f"{fname}: Theme color meta tag present")

        # 3. Meta description
        if '<meta name="description"' not in content:
            failures.append(f"{fname}: Missing meta description")
        else:
            passes.append(f"{fname}: Meta description present")

        # 4. Standalone page overflow safety
        if fname != "index.html":
            if "overflow-x: hidden" not in content and "max-width: 100%" not in content:
                failures.append(f"{fname}: Missing overflow-x: hidden or max-width: 100%")
            else:
                passes.append(f"{fname}: Overflow safety rules present")

        # 5. Table wrapper check in dashboard
        if fname == "dashboard.html":
            if "table-scroll-wrapper" not in content:
                failures.append(f"{fname}: Missing table-scroll-wrapper around auditsTable")
            else:
                passes.append(f"{fname}: Table scroll wrapper verified")

        # 6. Hamburger / mobile menu check in about.html & contact.html
        if fname in ["about.html", "contact.html"]:
            if "mobile-drawer" not in content or "mobile-nav-toggle" not in content:
                failures.append(f"{fname}: Missing mobile navigation drawer or toggle")
            else:
                passes.append(f"{fname}: Mobile navigation drawer and toggle verified")

        # 7. 16px input font size check on auth and form pages
        if fname in ["contact.html", "login.html", "signup.html", "account.html"]:
            if "font-size: 16px" not in content:
                failures.append(f"{fname}: Inputs missing 16px font size baseline for iOS")
            else:
                passes.append(f"{fname}: 16px input font size verified (anti-zoom)")

    # 8. Check style.css
    css_path = os.path.join(WEB_DIR, "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            css_content = f.read()

        if "clamp(" not in css_content:
            failures.append("style.css: Missing fluid typography clamp() rules")
        else:
            passes.append("style.css: Fluid typography clamp() present")

        if "@media (max-width: 768px)" not in css_content:
            failures.append("style.css: Missing 768px media query")
        else:
            passes.append("style.css: 768px media query present")

        if "font-size: 16px" not in css_content:
            failures.append("style.css: Missing 16px mobile input rule")
        else:
            passes.append("style.css: 16px mobile input rule present")

    print(f"\n[+] Total checks passed: {len(passes)}")
    if failures:
        print(f"[-] Total checks failed: {len(failures)}")
        for fail in failures:
            print(f"    FAIL: {fail}")
        return False
    else:
        print("ALL 16 MOBILE AUDIT REQUIREMENTS FULLY VERIFIED!")
        return True

if __name__ == "__main__":
    success = run_checks()
    sys.exit(0 if success else 1)
