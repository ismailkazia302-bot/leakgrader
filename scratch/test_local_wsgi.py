"""
Test WSGI locally with sys.path
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import io
from wsgi import application

def test_route(path, body):
    payload = json.dumps(body).encode('utf-8')
    environ = {
        'PATH_INFO': path,
        'REQUEST_METHOD': 'POST',
        'CONTENT_TYPE': 'application/json',
        'CONTENT_LENGTH': str(len(payload)),
        'wsgi.input': io.BytesIO(payload)
    }
    def start_response(status, headers):
        print(f"Status: {status}")
    resp = application(environ, start_response)
    print("Response:", b"".join(resp).decode('utf-8'))

print("--- TESTING LEADS ---")
test_route('/api/leads/generate', {"industry": "Real Estate", "location": "Dubai", "count": 2})

print("\n--- TESTING BOOKING CHAT ---")
test_route('/api/booking/chat', {"message": "Hi", "history": []})
