from src.tools import retrieve_legal_documents, set_knowledge_ids
from src.ragflow_client import RagFlowClient
import os

# Load env
from dotenv import load_dotenv
load_dotenv(override=True)

# Redirect output to file
with open("debug_output.txt", "w", encoding="utf-8") as f:
    # 1. Print current ID in Env
    f.write(f"Current ENV ID: {os.getenv('RAGFLOW_KNOWLEDGE_ID')}\n")

    # 2. List available datasets (to confirm connection)
    try:
        f.write("\n--- Listing Datasets ---\n")
        
        # Use requests directly as client lacks list_datasets
        import requests
        base_url = os.getenv("RAGFLOW_BASE_URL", "http://localhost/api")
        api_key = os.getenv("RAGFLOW_API_KEY")
        
        url = f"{base_url}/api/v1/datasets"
        headers = {"Authorization": f"Bearer {api_key}"}
        
        resp = requests.get(url, headers=headers)
        data = resp.json()
        
        if data.get('code') == 0:
            datasets = data.get('data', [])
            for d in datasets:
                f.write(f"ID: {d.get('id')} | Name: {d.get('name')} | Docs: {d.get('document_count')} | Chunks: {d.get('chunk_count')}\n")
        else:
            f.write(f"API Error: {data}\n")

    except Exception as e:
        f.write(f"Error listing datasets: {e}\n")

    # 3. Test Retrieval with a known keyword
    TARGET_ID = "22a2542ad30b11f0825df6ae2c1a0c2f" # legal systems
    
    # Try multiple queries
    queries = ["khoáng sản", "investment", "luật"]
    
    for q in queries:
        f.write(f"\n--- Query: '{q}' (Threshold 0.2) ---\n")
        try:
            from src.ragflow_client import RagFlowClient
            c = RagFlowClient()
            # Must lower the threshold to find ANYTHING
            pack = c.search(q, knowledge_ids=[TARGET_ID], similarity_threshold=0.2)
            
            f.write(f"Items found: {len(pack.items)}\n")
            for item in pack.items:
                f.write(f" - Doc: {item.document_name}\n")
                f.write(f"   Snippet: {item.content[:100]}...\n")
        except Exception as e:
            f.write(f"Error: {e}\n")

print("Debug complete. Check debug_output.txt")
