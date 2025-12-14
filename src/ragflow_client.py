import os
import requests
from typing import List, Optional
from tenacity import retry, stop_after_attempt, wait_fixed
from src.schemas import EvidenceItem, EvidencePack

class RagFlowClient:
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = base_url or os.getenv("RAGFLOW_BASE_URL", "http://localhost/api")
        self.api_key = api_key or os.getenv("RAGFLOW_API_KEY")
        
        if not self.api_key:
            # Depending on RAGFlow setup, API key might be optional or required.
            # Warning only for now.
            print("Warning: RAGFLOW_API_KEY not set in client init.")
        else:
            print(f"DEBUG: Client initialized with API Key: {self.api_key[:5]}...")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}" if self.api_key else "",
            "Content-Type": "application/json"
        }

    # @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def search(self, query: str, top_k: int = 5, similarity_threshold: float = 0.5, knowledge_ids: Optional[List[str]] = None) -> EvidencePack:
        """
        Search for documents in RAGFlow.
        Assumes RAGFlow exposes an endpoint like /v1/retrieval or /api/completion depending on setup.
        For this implementation, we assume a standard /retrieval endpoint or similar.
        
        NOTE: You may need to adjust the ENDPOINT and payload format to match your specific RAGFlow version.
        """
        # Placeholder endpoint - ADJUST THIS based on actual RAGFlow API docs
        # Common RAGFlow path is /api/v1/retrieval
        endpoint = f"{self.base_url}/api/v1/retrieval" 
        print(f"DEBUG: Querying endpoint: {endpoint}")
        
        # Resolve knowledge_ids: argument > env var > error
        if not knowledge_ids:
            env_ids = os.getenv("RAGFLOW_KNOWLEDGE_ID")
            if env_ids:
                knowledge_ids = [k.strip() for k in env_ids.split(",")]
            else:
                 print("Warning: No knowledge_ids provided and RAGFLOW_KNOWLEDGE_ID not set.")
                 # Some versions of RAGFlow might require this field.
                 knowledge_ids = []

        payload = {
            "question": query,
            "top_k": top_k,
            "similarity_threshold": similarity_threshold,
            "dataset_ids": knowledge_ids  # RAGFlow API expects 'dataset_ids' not 'knowledge_ids'
        }

        try:
            # Example call - replace with actual RAGFlow SDK or API logic
            response = requests.post(endpoint, json=payload, headers=self.headers, timeout=30)
            print(f"DEBUG: Response status: {response.status_code}")
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                print(f"DEBUG: HTTP Error: {e}")
                print(f"DEBUG: Response content: {response.text}")
                raise

            data = response.json()
            print(f"DEBUG: Raw RAGFlow response keys: {data.keys()}")
            print(f"DEBUG: Raw RAGFlow response: {repr(data)}")
            
            # Map response to EvidencePack
            # RAGFlow returns: {'code': 0, 'data': {'chunks': [{'content': '...', 'chunk_id': '...', 'doc_name': '...'}]}}
            
            items = []
            if data.get("code") == 0 and "data" in data:
                data_content = data["data"]
                
                # Handle format: {'data': {'chunks': [...]}}
                if isinstance(data_content, dict) and "chunks" in data_content:
                    for doc in data_content["chunks"]:
                        item = EvidenceItem(
                            content=doc.get("content_with_weight", doc.get("content", "")),
                            document_name=doc.get("doc_name", doc.get("document_keyword", "Unknown Document")),
                            chunk_id=doc.get("chunk_id"),
                            similarity_score=doc.get("similarity"),
                            original_metadata=doc
                        )
                        items.append(item)
                # Handle format: {'data': [...]} (legacy)
                elif isinstance(data_content, list):
                    for doc in data_content:
                        item = EvidenceItem(
                            content=doc.get("content_with_weight", doc.get("content", "")),
                            document_name=doc.get("doc_name", "Unknown Document"),
                            chunk_id=doc.get("chunk_id"),
                            similarity_score=doc.get("similarity"),
                            original_metadata=doc
                        )
                        items.append(item)
                # Handle format: {'data': {'docs': [...]}}
                elif isinstance(data_content, dict) and "docs" in data_content:
                    for doc in data_content["docs"]:
                        item = EvidenceItem(
                            content=doc.get("content_with_weight", doc.get("content", "")),
                            document_name=doc.get("doc_name", "Unknown Document"),
                            chunk_id=doc.get("chunk_id"),
                            similarity_score=doc.get("similarity"),
                            original_metadata=doc
                        )
                        items.append(item)
                else:
                    print(f"DEBUG: 'data' field structure unknown: {type(data_content)}, keys: {data_content.keys() if isinstance(data_content, dict) else 'N/A'}")
            
            return EvidencePack(query=query, items=items, total_items=len(items))

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error querying RAGFlow: {e}")
            # Return empty pack on failure to avoid crashing the agent
            return EvidencePack(query=query, items=[], total_items=0)
