#!/usr/bin/env python3
"""
Quick cURL test script for Publishing API

Automatically uses environment variables and generates test requests.
"""

import os
import json
import subprocess
import sys
from dotenv import load_dotenv

load_dotenv()

def run_curl(endpoint, method="GET", headers=None, data=None):
    """Run curl command and return result."""
    cmd = ["curl", "-X", method]
    
    if headers:
        for key, value in headers.items():
            cmd.extend(["-H", f"{key}: {value}"])
    
    if data:
        cmd.extend(["-d", json.dumps(data)])
    
    cmd.append(f"http://localhost:8000{endpoint}")
    
    print(f"Running: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(f"Status Code: {result.returncode}")
        print(f"Response: {result.stdout}")
        if result.stderr:
            print(f"Error: {result.stderr}")
        return result.returncode == 0
    except FileNotFoundError:
        print("❌ curl not found. Using Python requests instead...")
        return False

def test_with_requests():
    """Fallback to Python requests if curl not available."""
    try:
        import requests
    except ImportError:
        print("❌ Neither curl nor requests available")
        return False
    
    # Health check
    print("🏥 Testing health endpoint...")
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Test publish endpoint
    api_key = os.getenv("API_KEY")
    user_id = os.getenv("DISCORD_USER_ID")
    
    if not api_key or not user_id:
        print("❌ Missing API_KEY or DISCORD_USER_ID environment variables")
        return False
    
    print("\n📝 Testing publish endpoint...")
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }
    
    data = {
        "message": """/post note
---
title: Test Note from Python Script
tags: ["test", "python", "api"]
---

This is a **test note** published via Python requests!

## Test Details

- Timestamp: 2025-08-08T20:30:00Z
- Method: Python requests library
- Endpoint: /publish

Successfully testing the API! 🎉""",
        "user_id": user_id
    }
    
    try:
        response = requests.post("http://localhost:8000/publish", headers=headers, json=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Publish test failed: {e}")
        return False

def main():
    """Main test function."""
    print("🧪 Publishing API Test Script")
    print("=" * 40)
    
    # Check environment variables
    api_key = os.getenv("API_KEY")
    user_id = os.getenv("DISCORD_USER_ID")
    
    if not api_key:
        print("❌ API_KEY environment variable not found")
        return 1
    
    if not user_id:
        print("❌ DISCORD_USER_ID environment variable not found")
        return 1
    
    print(f"✅ API Key: {api_key[:8]}...")
    print(f"✅ User ID: {user_id}")
    
    # Test health endpoint
    print("\n🏥 Testing health endpoint...")
    success = run_curl("/health")
    
    if success:
        print("✅ Health check passed")
    else:
        print("⚠️ curl failed, trying Python requests...")
        if not test_with_requests():
            return 1
        return 0
    
    # Test publish endpoint
    print("\n📝 Testing publish endpoint...")
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }
    
    data = {
        "message": """/post note
---
title: Test Note from cURL Script
tags: ["test", "curl", "automation"]
---

This is a **test note** published via cURL!

## Test Information

- Date: 2025-08-08
- Method: cURL command
- Script: Automated test

API integration working perfectly! ✅""",
        "user_id": user_id
    }
    
    success = run_curl("/publish", "POST", headers, data)
    
    if success:
        print("✅ Publish test passed")
        return 0
    else:
        print("❌ Publish test failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
