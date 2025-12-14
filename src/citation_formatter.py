"""
Citation Formatter for Vietnamese Legal Documents

This module provides utilities for formatting legal citations in both
Vietnamese and English, following standard legal citation conventions.
"""
import re
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum


class DocumentType(Enum):
    """Types of Vietnamese legal documents."""
    LAW = "Luật"  # Laws passed by National Assembly
    DECREE = "Nghị định"  # Government decrees
    CIRCULAR = "Thông tư"  # Ministry circulars
    RESOLUTION = "Nghị quyết"  # Resolutions
    DECISION = "Quyết định"  # Decisions
    DIRECTIVE = "Chỉ thị"  # Directives
    UNKNOWN = "Unknown"


@dataclass
class Citation:
    """Structured representation of a legal citation."""
    document_type: DocumentType
    document_number: str
    year: int
    issuing_body: str
    article: Optional[int] = None
    clause: Optional[int] = None
    point: Optional[str] = None  # e.g., "a", "b", "c"
    document_title: Optional[str] = None
    
    def to_vietnamese(self) -> str:
        """Format citation in Vietnamese style."""
        parts = []
        
        # Article/Clause/Point reference
        if self.point:
            parts.append(f"Điểm {self.point}")
        if self.clause:
            parts.append(f"Khoản {self.clause}")
        if self.article:
            parts.append(f"Điều {self.article}")
        
        # Document reference
        doc_ref = f"{self.document_type.value} số {self.document_number}/{self.year}/{self.issuing_body}"
        parts.append(doc_ref)
        
        if self.document_title:
            parts.append(f"({self.document_title})")
        
        return " ".join(parts)
    
    def to_english(self) -> str:
        """Format citation in English style."""
        type_map = {
            DocumentType.LAW: "Law",
            DocumentType.DECREE: "Decree",
            DocumentType.CIRCULAR: "Circular",
            DocumentType.RESOLUTION: "Resolution",
            DocumentType.DECISION: "Decision",
            DocumentType.DIRECTIVE: "Directive",
            DocumentType.UNKNOWN: "Document",
        }
        
        parts = []
        
        # Article/Clause/Point reference
        if self.point:
            parts.append(f"Point {self.point}")
        if self.clause:
            parts.append(f"Clause {self.clause}")
        if self.article:
            parts.append(f"Article {self.article}")
        
        # Document reference
        doc_type = type_map.get(self.document_type, "Document")
        doc_ref = f"{doc_type} No. {self.document_number}/{self.year}/{self.issuing_body}"
        parts.append(doc_ref)
        
        if self.document_title:
            parts.append(f"({self.document_title})")
        
        return ", ".join(parts)


def detect_document_type(doc_id: str) -> DocumentType:
    """Detect document type from document ID suffix."""
    doc_id_upper = doc_id.upper()
    
    if "QH" in doc_id_upper:  # National Assembly (Quốc Hội)
        return DocumentType.LAW
    elif "ND-CP" in doc_id_upper or "NĐ-CP" in doc_id_upper:  # Government Decree
        return DocumentType.DECREE
    elif "TT-" in doc_id_upper:  # Circular
        return DocumentType.CIRCULAR
    elif "NQ-" in doc_id_upper:  # Resolution
        return DocumentType.RESOLUTION
    elif "QD-" in doc_id_upper or "QĐ-" in doc_id_upper:  # Decision
        return DocumentType.DECISION
    elif "CT-" in doc_id_upper:  # Directive
        return DocumentType.DIRECTIVE
    else:
        return DocumentType.UNKNOWN


def parse_citation(text: str) -> Optional[Citation]:
    """
    Parse a citation string into a structured Citation object.
    
    Supports formats like:
    - "Điều 28, Luật số 60/2010/QH12"
    - "Article 28, Law No. 60/2010/QH12"
    - "Khoản 1 Điều 53 Luật Khoáng sản 2010"
    """
    # Pattern for Vietnamese style: "Điều X Luật/Nghị định số Y/YEAR/BODY"
    vn_pattern = r'(?:Điểm\s+([a-z]))?[\s,]*(?:Khoản\s+(\d+))?[\s,]*(?:Điều\s+(\d+))?[\s,]*(?:Luật|Nghị định|Thông tư)\s+(?:số\s+)?(\d+)/(\d{4})/([A-Z\-]+\d*)'
    
    # Pattern for English style: "Article X, Law/Decree No. Y/YEAR/BODY"
    en_pattern = r'(?:Point\s+([a-z]))?[\s,]*(?:Clause\s+(\d+))?[\s,]*(?:Article\s+(\d+))?[\s,]*(?:Law|Decree|Circular)\s+(?:No\.\s*)?(\d+)/(\d{4})/([A-Z\-]+\d*)'
    
    for pattern in [vn_pattern, en_pattern]:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            groups = match.groups()
            point = groups[0]
            clause = int(groups[1]) if groups[1] else None
            article = int(groups[2]) if groups[2] else None
            doc_num = groups[3]
            year = int(groups[4])
            issuing_body = groups[5]
            
            doc_id = f"{doc_num}/{year}/{issuing_body}"
            doc_type = detect_document_type(doc_id)
            
            return Citation(
                document_type=doc_type,
                document_number=doc_num,
                year=year,
                issuing_body=issuing_body,
                article=article,
                clause=clause,
                point=point,
            )
    
    return None


def format_footnote(citation: Citation, footnote_num: int) -> str:
    """Format a citation as a footnote reference."""
    return f"[^{footnote_num}]: {citation.to_vietnamese()}"


def format_inline(citation: Citation) -> str:
    """Format a citation for inline use."""
    return f"({citation.to_english()})"


def extract_and_format_citations(text: str, format_type: str = "english") -> str:
    """
    Extract citations from text and reformat them consistently.
    
    Args:
        text: The text containing citations.
        format_type: "vietnamese" or "english"
    
    Returns:
        Text with reformatted citations.
    """
    # Find all potential citation patterns
    citation_patterns = [
        r'(?:Điều|Article)\s+\d+[^.]*?(?:Luật|Law|Nghị định|Decree)[^.]*?\d+/\d{4}/[A-Z\-]+\d*',
    ]
    
    result = text
    for pattern in citation_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            original = match.group(0)
            parsed = parse_citation(original)
            if parsed:
                if format_type == "vietnamese":
                    formatted = parsed.to_vietnamese()
                else:
                    formatted = parsed.to_english()
                result = result.replace(original, formatted, 1)
    
    return result


def create_bibliography(citations: List[Citation]) -> str:
    """
    Create a bibliography section from a list of citations.
    """
    # Group by document type
    by_type: Dict[DocumentType, List[Citation]] = {}
    for c in citations:
        if c.document_type not in by_type:
            by_type[c.document_type] = []
        by_type[c.document_type].append(c)
    
    lines = ["## References\n"]
    
    type_order = [DocumentType.LAW, DocumentType.DECREE, DocumentType.CIRCULAR, 
                  DocumentType.RESOLUTION, DocumentType.DECISION, DocumentType.DIRECTIVE]
    
    for doc_type in type_order:
        if doc_type in by_type:
            lines.append(f"### {doc_type.value}s")
            # Sort by year, then number
            sorted_cites = sorted(by_type[doc_type], key=lambda x: (x.year, x.document_number))
            for c in sorted_cites:
                lines.append(f"- {c.to_vietnamese()}")
            lines.append("")
    
    return "\n".join(lines)


if __name__ == "__main__":
    # Test the module
    print("Testing citation parsing and formatting...\n")
    
    test_texts = [
        "Điều 28, Luật số 60/2010/QH12",
        "Article 53, Law No. 60/2010/QH12 on Minerals",
        "Khoản 1 Điều 55 Nghị định số 15/2012/ND-CP",
        "Point a, Clause 2, Article 70, Decree No. 40/2019/ND-CP",
    ]
    
    for text in test_texts:
        citation = parse_citation(text)
        if citation:
            print(f"Original: {text}")
            print(f"  Vietnamese: {citation.to_vietnamese()}")
            print(f"  English: {citation.to_english()}")
            print()
        else:
            print(f"Could not parse: {text}\n")
