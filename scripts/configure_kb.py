import os
import requests
from dotenv import load_dotenv, find_dotenv, set_key

def configure_kb():
    # Load env vars
    dotenv_path = find_dotenv()
    if not dotenv_path:
        # If no .env exists, create one in current dir
        dotenv_path = os.path.join(os.getcwd(), '.env')
        if not os.path.exists(dotenv_path):
             with open(dotenv_path, 'w') as f:
                 f.write("")
    
    load_dotenv(dotenv_path, override=True)
    
    api_key = os.getenv("RAGFLOW_API_KEY")
    base_url = os.getenv("RAGFLOW_BASE_URL", "http://localhost:9380")
    
    if not api_key:
        print("Error: RAGFLOW_API_KEY is not set in .env")
        return

    print("--- RAGFlow Knowledge Base Configuration ---")
    print(f"Fetching Knowledge Bases from {base_url}...")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Try singular and plural endpoints to be safe
    endpoints = [
        f"{base_url}/api/v1/datasets",
        f"{base_url}/api/v1/dataset"
    ]
    
    datasets = []
    
    for endpoint in endpoints:
        try:
            response = requests.get(endpoint, headers=headers, params={"page": 1, "page_size": 100}, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 0 and "data" in data:
                    raw_data = data["data"]
                    # Handle both list and dict pagination format
                    if isinstance(raw_data, list):
                        datasets = raw_data
                    elif isinstance(raw_data, dict) and "docs" in raw_data:
                         datasets = raw_data["docs"]
                    
                    if datasets:
                        break # Successfully found datasets
        except Exception:
            continue
            
    if not datasets:
        print("No Knowledge Bases found or connection failed.")
        return

    print("\nAvailable Knowledge Bases:")
    for i, kb in enumerate(datasets):
        name = kb.get('name', 'Unnamed')
        kb_id = kb.get('id')
        print(f"{i + 1}. {name} (ID: {kb_id})")
        
    print("\n")
    while True:
        choice = input("Select a Knowledge Base by number: ")
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(datasets):
                selected_kb = datasets[idx]
                selected_id = selected_kb.get('id')
                selected_name = selected_kb.get('name')
                
                print(f"\nYou selected: {selected_name}")
                
                # Save to .env
                set_key(dotenv_path, "RAGFLOW_KNOWLEDGE_ID", selected_id)
                print(f"Success! Updated RAGFLOW_KNOWLEDGE_ID in {dotenv_path}")
                break
            else:
                print("Invalid number. Please try again.")
        except ValueError:
            print("Please enter a valid number.")

if __name__ == "__main__":
    configure_kb()
