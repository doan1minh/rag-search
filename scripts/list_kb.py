import os
import requests
from dotenv import load_dotenv, find_dotenv

def list_knowledge_bases():
    load_dotenv(find_dotenv(), override=True)
    
    api_key = os.getenv("RAGFLOW_API_KEY")
    base_url = os.getenv("RAGFLOW_BASE_URL", "http://localhost:9380")
    
    # Try common endpoints
    endpoints = [
        f"{base_url}/api/v1/datasets",
        f"{base_url}/api/v1/dataset",
        f"{base_url}/v1/dataset",
        f"{base_url}/api/dataset"
    ]
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    print(f"DEBUG: Using API Key: {api_key[:5]}...")
    
    for endpoint in endpoints:
        print(f"\nTrying endpoint: {endpoint}")
        try:
            response = requests.get(endpoint, headers=headers, params={"page": 1, "page_size": 100}, timeout=10)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Success! Data: {data}")
                if data.get("code") == 0 and "data" in data:
                     for kb in data["data"]:
                        print(f"Found KB: {kb.get('name')} - ID: {kb.get('id')}")
                return
            else:
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    list_knowledge_bases()
