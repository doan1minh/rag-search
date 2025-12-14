import os
import requests
from dotenv import load_dotenv, find_dotenv

def list_documents():
    load_dotenv(find_dotenv(), override=True)
    
    api_key = os.getenv("RAGFLOW_API_KEY")
    base_url = os.getenv("RAGFLOW_BASE_URL", "http://localhost:9380")
    kb_id = os.getenv("RAGFLOW_KNOWLEDGE_ID")
    
    if not api_key:
        print("Error: RAGFLOW_API_KEY env var not set")
        return
    if not kb_id:
        print("Error: RAGFLOW_KNOWLEDGE_ID env var not set")
        return
        
    print(f"--- Listing documents for KB ID: {kb_id} ---")
    
    # Try singular and plural forms for endpoint robustness
    endpoints = [
        f"{base_url}/api/v1/datasets/{kb_id}/documents",
        f"{base_url}/api/v1/dataset/{kb_id}/documents",
        f"{base_url}/v1/dataset/{kb_id}/document", 
        f"{base_url}/api/v1/dataset/{kb_id}/document" # Possible variations
    ]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    for endpoint in endpoints:
        print(f"Trying endpoint: {endpoint}")
        try:
            response = requests.get(endpoint, headers=headers, params={"page": 1, "page_size": 20}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"Success! Response: {data}")
                
                docs = []
                if data.get("code") == 0 and "data" in data:
                    # Handle pagination format
                    if isinstance(data["data"], dict) and "docs" in data["data"]:
                        docs = data["data"]["docs"]
                    elif isinstance(data["data"], list):
                         docs = data["data"]
                
                print(f"\nFound {len(docs)} documents:")
                for doc in docs:
                    print(f"- {doc.get('name')} (ID: {doc.get('id')}, Rows: {doc.get('chunk_num')})")
                return
            else:
                 print(f"Status {response.status_code}: {response.text}")

        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    list_documents()
