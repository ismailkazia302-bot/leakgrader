import urllib.request
import urllib.error
import ssl
import sys

ctx = ssl.create_default_context()

mobile_headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
}

all_passed = True

print("==================================================")
print("LIVE POST-DEPLOYMENT VERIFICATION (PHASE 3)")
print("==================================================")

# 1. Check Homepage on mobile
req_home = urllib.request.Request('https://leakgrader.com/', headers=mobile_headers)
try:
    with urllib.request.urlopen(req_home, context=ctx, timeout=20) as resp:
        status = resp.status
        body = resp.read().decode('utf-8', errors='ignore')
        has_theme = 'theme-color' in body
        has_viewport = 'viewport' in body
        print(f"[PASS] Homepage loaded: HTTP {status}")
        print(f"       Viewport tag verified: {has_viewport}")
        print(f"       Theme color tag verified: {has_theme}")
        if status != 200:
            all_passed = False
except Exception as e:
    print(f"[FAIL] Homepage request failed: {e}")
    all_passed = False

# 2. Check /founder endpoint (must be 404)
req_founder = urllib.request.Request('https://leakgrader.com/founder', headers=mobile_headers)
try:
    with urllib.request.urlopen(req_founder, context=ctx, timeout=20) as resp:
        print(f"[FAIL] /founder returned HTTP {resp.status} (expected 404)")
        all_passed = False
except urllib.error.HTTPError as e:
    if e.code == 404:
        print(f"[PASS] /founder hidden: HTTP {e.code} (Lockdown verified)")
    else:
        print(f"[WARN] /founder returned HTTP {e.code} (expected 404)")
        all_passed = False
except Exception as e:
    print(f"[FAIL] /founder error: {e}")
    all_passed = False

# 3. Check health endpoint
req_health = urllib.request.Request('https://leakgrader.com/health', headers=mobile_headers)
try:
    with urllib.request.urlopen(req_health, context=ctx, timeout=20) as resp:
        status = resp.status
        content = resp.read().decode('utf-8')
        print(f"[PASS] Health check: HTTP {status} -> {content.strip()}")
        if status != 200:
            all_passed = False
except Exception as e:
    print(f"[FAIL] Health check failed: {e}")
    all_passed = False

print("==================================================")
if all_passed:
    print("VERDICT: MOBILE_DEPLOYED_SUCCESSFULLY")
    sys.exit(0)
else:
    print("VERDICT: DEPLOYMENT_VERIFICATION_FAILED")
    sys.exit(1)
