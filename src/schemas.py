from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class EvidenceItem(BaseModel):
    """
    Represents a single piece of evidence retrieved from the knowledge base.
    """
    content: str = Field(..., description="The exact text content/quote from the document")
    document_name: str = Field(..., description="Name of the source document (e.g. 'Luật Đất đai 2024')")
    
    # Metadata fields mapping to RAGFlow outputs
    chunk_id: Optional[str] = Field(None, description="Unique ID of the chunk")
    similarity_score: Optional[float] = Field(None, description="Relevance score")
    
    # Legal specific metadata (to be extracted or populated if available)
    issuing_authority: Optional[str] = Field(None, description="Agency that issued the document")
    effective_date: Optional[str] = Field(None, description="Date the document became effective")
    legal_reference: Optional[str] = Field(None, description="Article/Clause reference (e.g. 'Dieu 5, Khoan 2')")
    is_valid: Optional[bool] = Field(None, description="Whether the document is currently legally valid")
    
    original_metadata: Dict[str, Any] = Field(default_factory=dict, description="Raw metadata from RAGFlow")

class EvidencePack(BaseModel):
    """
    A collection of evidence items relevant to a specific query.
    """
    query: str = Field(..., description="The query used to retrieve this evidence")
    items: List[EvidenceItem] = Field(..., description="List of evidence items")
    total_items: int = Field(..., description="Number of items retrieved")
