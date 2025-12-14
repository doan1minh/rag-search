import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools import retrieve_legal_documents
from dotenv import load_dotenv, find_dotenv

def main():
    load_dotenv(find_dotenv(), override=True)
    print("--- Verifying RAGFlow Integration ---")
    
    print(f"DEBUG: RAGFLOW_KNOWLEDGE_ID from env: {os.getenv('RAGFLOW_KNOWLEDGE_ID')}")
    query = "rừng đặc dụng"
    print(f"Querying: '{query}'")
    
    try:
        result = retrieve_legal_documents(query)
        
        items = result.get("items", [])
        print(f"Found {len(items)} items.")
        
        if len(items) == 0:
            print("WARNING: No items returned. Check RAGFlow connection and content.")
        
        for i, item in enumerate(items):
            print(f"\n[{i+1}] Source: {item.get('document_name')}")
            print(f"    Content: {item.get('content')[:100]}...")
            print(f"    Score: {item.get('similarity_score')}")
            
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    main()
