# test_session_endpoint.py
import asyncio
import httpx
import json
import os
from dotenv import load_dotenv

# Load environment variables (if you're using them)
load_dotenv()

# Configuration
BASE_URL = "http://localhost:8000"  # Change this to your server URL
API_PATH = "/api/v1/sessions/create"
TOKEN = ""  # Add a valid faculty token here

async def test_create_session():
    """Test the session creation endpoint directly."""
    # Headers with authentication
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Request body - use the same format your Android app uses
    payload = {
        "course_code": "CS101",
        "room_number": "R101"
    }
    
    url = f"{BASE_URL}{API_PATH}"
    
    print(f"Making request to: {url}")
    print(f"Payload: {payload}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url, 
                headers=headers,
                json=payload,
                timeout=30.0
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {response.headers}")
            
            if response.status_code == 200:
                print("Success! Response:")
                print(json.dumps(response.json(), indent=2))
            else:
                print(f"Error! Response:")
                print(response.text)
                
        except Exception as e:
            print(f"Request failed: {str(e)}")

if __name__ == "__main__":
    # Get a valid token first
    print("To get a token, login with a faculty account first")
    email = input("Faculty email: ")
    password = input("Password: ")
    
    # Login to get token
    login_payload = {
        "username": email,
        "password": password
    }
    
    # Run login request in sync mode for simplicity
    try:
        login_response = httpx.post(
            f"{BASE_URL}/api/v1/auth/login",
            data=login_payload,
            timeout=30.0
        )
        
        if login_response.status_code == 200:
            token_data = login_response.json()
            TOKEN = token_data.get("access_token")
            print(f"Login successful! Token: {TOKEN[:10]}...")
        else:
            print(f"Login failed: {login_response.text}")
            exit(1)
    except Exception as e:
        print(f"Login request failed: {str(e)}")
        exit(1)
    
    # Run the test
    asyncio.run(test_create_session())