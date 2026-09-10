import subprocess
import time
import urllib.request
import urllib.error
import os
import sys

port = 8199
env = os.environ.copy()
env['ENVIRONMENT'] = 'production'
env['SECURITY_LOCKDOWN_MODE'] = 'enabled'
env['LOCKDOWN_PHASE'] = 'full'
env['PORT'] = str(port)

server_code = f"from wsgi import app; from wsgiref.simple_server import make_server; make_server('127.0.0.1', {port}, app).serve_forever()"

proc = subprocess.Popen([
    sys.executable, '-c', server_code
], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

time.sleep(2.5)

def test_req(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 Test'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = resp.read()
            print(f"{url} -> HTTP {resp.status} (bytes: {len(data)}) | Body preview: {data[:60]}")
    except urllib.error.HTTPError as e:
        data = e.read()
        print(f"{url} -> HTTP {e.code} (bytes: {len(data)}) | Body preview: {data[:60]}")

try:
    print("Testing local server (wsgi.app) on port", port)
    test_req(f"http://127.0.0.1:{port}/api/leads/list")
    test_req(f"http://127.0.0.1:{port}/wp-admin/install.php?step=1")
    test_req(f"http://127.0.0.1:{port}/.env")
    test_req(f"http://127.0.0.1:{port}/api/booking/list")
    test_req(f"http://127.0.0.1:{port}/founder")
    test_req(f"http://127.0.0.1:{port}/")
finally:
    proc.terminate()
    proc.wait()

# Also verify wsgi:application (Gunicorn default PEP-3333 entrypoint)
port2 = 8198
server_code2 = f"from wsgi import application; from wsgiref.simple_server import make_server; make_server('127.0.0.1', {port2}, application).serve_forever()"
proc2 = subprocess.Popen([
    sys.executable, '-c', server_code2
], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2.5)
try:
    print("\nTesting local server (wsgi.application) on port", port2)
    test_req(f"http://127.0.0.1:{port2}/api/leads/list")
    test_req(f"http://127.0.0.1:{port2}/wp-admin/install.php?step=1")
    test_req(f"http://127.0.0.1:{port2}/.env")
    test_req(f"http://127.0.0.1:{port2}/")
finally:
    proc2.terminate()
    proc2.wait()
