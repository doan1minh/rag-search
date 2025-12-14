from typing import Annotated, List, Optional
from src.ragflow_client import RagFlowClient
from src.schemas import EvidencePack

# Initialize client globally or within the function (global is better for caching connection if needed)
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(), override=True) # Ensure env vars are loaded before client init
client = RagFlowClient()

# Global configuration for knowledge base IDs (can be set from notebook)
# This allows runtime selection of RAGFlow databases without modifying .env
_knowledge_ids: Optional[List[str]] = None

def set_knowledge_ids(ids: Optional[List[str]]):
    """Set the knowledge base IDs to use for retrieval. Call this before running research."""
    global _knowledge_ids
    _knowledge_ids = ids
    print(f"✅ RAGFlow knowledge IDs set to: {ids}")

def get_knowledge_ids() -> Optional[List[str]]:
    """Get the currently configured knowledge base IDs."""
    return _knowledge_ids

def retrieve_legal_documents(
    query: Annotated[str, "The search query to find legal documents and evidence"],
) -> dict:
    """
    Search for legal documents, laws, decrees, and circulars relevant to the query.
    Returns a structured package of evidence containing quotes and metadata.
    """
    print(f"[TOOL] Retrieving documents for: {query}")
    pack: EvidencePack = client.search(query=query, top_k=10, knowledge_ids=_knowledge_ids)
    
    # Return as dict for AutoGen compatibility
    return pack.model_dump()


from duckduckgo_search import DDGS

def search_legal_updates(query: Annotated[str, "Tên văn bản hoặc từ khóa pháp lý để kiểm tra hiệu lực"]) -> str:
    """
    Tìm kiếm trên web để kiểm tra hiệu lực văn bản pháp luật hoặc tìm văn bản thay thế mới nhất.
    Sử dụng tool này khi cần xác minh thông tin pháp lý từ RAGFlow có còn hiệu lực hay không.
    """
    print(f"[TOOL] Web searching for: {query}")
    try:
        results = DDGS().text(keywords=f"hiệu lực văn bản {query} thuvienphapluat vanbanphapluat", max_results=5)
        if not results:
            return "Không tìm thấy thông tin trên web."
        
        evidence = []
        for r in results:
            evidence.append(f"Title: {r['title']}\nLink: {r['href']}\nSnippet: {r['body']}")
        
        return "\n---\n".join(evidence)
    except Exception as e:
        return f"Lỗi khi search web: {str(e)}"
