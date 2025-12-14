"""
Effective Date Checker for Legal Documents

This module validates whether legal documents cited in research outputs 
are still in effect or have been superseded/repealed.
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class LegalDocumentStatus:
    """Status of a legal document."""
    document_name: str
    document_id: Optional[str] = None  # e.g., "60/2010/QH12"
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    is_active: bool = True
    superseded_by: Optional[str] = None
    notes: Optional[str] = None


def parse_document_id(document_name: str) -> Optional[str]:
    """
    Extract document ID from a document name.
    
    Examples:
        "Law No. 60/2010/QH12" -> "60/2010/QH12"
        "Decree No. 15/2012/ND-CP" -> "15/2012/ND-CP"
        "Circular No. 38/2015/TT-BTNMT" -> "38/2015/TT-BTNMT"
    """
    # Pattern for Vietnamese legal document IDs
    patterns = [
        r'(\d+/\d{4}/QH\d+)',           # Laws: 60/2010/QH12
        r'(\d+/\d{4}/ND-CP)',           # Decrees: 15/2012/ND-CP
        r'(\d+/\d{4}/TT-[A-Z]+)',       # Circulars: 38/2015/TT-BTNMT
        r'(\d+/\d{4}/NQ-[A-Z]+)',       # Resolutions
        r'(\d+/\d{4}/QD-[A-Z]+)',       # Decisions
    ]
    
    for pattern in patterns:
        match = re.search(pattern, document_name, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def extract_year_from_id(doc_id: str) -> Optional[int]:
    """Extract the year from a document ID."""
    match = re.search(r'/(\d{4})/', doc_id)
    if match:
        return int(match.group(1))
    return None


# Known supersession mappings (can be expanded or loaded from a database)
SUPERSESSION_DATABASE: Dict[str, Dict[str, Any]] = {
    # Law on Minerals
    "60/2010/QH12": {
        "name": "Law on Minerals 2010",
        "effective_date": date(2011, 7, 1),
        "is_active": True,
        "supersedes": "47/2005/QH11",  # Old Minerals Law
    },
    "47/2005/QH11": {
        "name": "Law on Minerals 2005",
        "effective_date": date(2006, 1, 1),
        "expiry_date": date(2011, 6, 30),
        "is_active": False,
        "superseded_by": "60/2010/QH12",
    },
    # Decrees
    "15/2012/ND-CP": {
        "name": "Decree detailing the Law on Minerals",
        "effective_date": date(2012, 5, 1),
        "is_active": True,
    },
    "40/2019/ND-CP": {
        "name": "Decree amending environmental regulations",
        "effective_date": date(2019, 7, 1),
        "is_active": True,
    },
}


def check_document_status(document_name: str, reference_date: Optional[date] = None) -> LegalDocumentStatus:
    """
    Check the status of a legal document.
    
    Args:
        document_name: The name or citation of the document.
        reference_date: The date to check effectiveness against (defaults to today).
    
    Returns:
        LegalDocumentStatus with validity information.
    """
    if reference_date is None:
        reference_date = date.today()
    
    doc_id = parse_document_id(document_name)
    
    status = LegalDocumentStatus(
        document_name=document_name,
        document_id=doc_id,
    )
    
    if doc_id and doc_id in SUPERSESSION_DATABASE:
        db_entry = SUPERSESSION_DATABASE[doc_id]
        status.effective_date = db_entry.get("effective_date")
        status.expiry_date = db_entry.get("expiry_date")
        status.is_active = db_entry.get("is_active", True)
        status.superseded_by = db_entry.get("superseded_by")
        
        # Check if expired by reference date
        if status.expiry_date and reference_date > status.expiry_date:
            status.is_active = False
            status.notes = f"Expired on {status.expiry_date}"
        
        if status.superseded_by:
            status.notes = f"Superseded by {status.superseded_by}"
    else:
        # Unknown document - assume active but flag for review
        year = extract_year_from_id(doc_id) if doc_id else None
        if year:
            # Heuristic: Documents older than 15 years may need verification
            if reference_date.year - year > 15:
                status.notes = "Document is older than 15 years; verify current status."
            status.is_active = True  # Assume active unless proven otherwise
        else:
            status.notes = "Could not parse document ID; manual verification required."
    
    return status


def validate_citations(citations: List[str]) -> List[LegalDocumentStatus]:
    """
    Validate a list of legal citations.
    
    Args:
        citations: List of document names or citations.
    
    Returns:
        List of LegalDocumentStatus objects.
    """
    results = []
    for citation in citations:
        status = check_document_status(citation)
        results.append(status)
        
        if not status.is_active:
            logger.warning(f"Citation '{citation}' may no longer be in effect: {status.notes}")
    
    return results


def format_validation_report(statuses: List[LegalDocumentStatus]) -> str:
    """
    Format validation results into a human-readable report.
    """
    lines = ["## Citation Validity Report\n"]
    
    active_count = sum(1 for s in statuses if s.is_active)
    inactive_count = len(statuses) - active_count
    
    lines.append(f"**Total Citations:** {len(statuses)}")
    lines.append(f"**Active:** {active_count} | **Inactive/Unknown:** {inactive_count}\n")
    
    for status in statuses:
        icon = "✅" if status.is_active else "⚠️"
        lines.append(f"- {icon} **{status.document_name}**")
        if status.document_id:
            lines.append(f"  - ID: `{status.document_id}`")
        if status.effective_date:
            lines.append(f"  - Effective: {status.effective_date}")
        if status.notes:
            lines.append(f"  - Note: {status.notes}")
    
    return "\n".join(lines)


# Convenience function for integration with agents
def check_citations_from_text(text: str) -> str:
    """
    Extract and validate citations from a block of text.
    Returns a formatted report.
    """
    # Simple extraction of document references
    patterns = [
        r'Law (?:No\.\s*)?\d+/\d{4}/QH\d+',
        r'Decree (?:No\.\s*)?\d+/\d{4}/ND-CP',
        r'Circular (?:No\.\s*)?\d+/\d{4}/TT-[A-Z]+',
        r'Luật số \d+/\d{4}/QH\d+',
        r'Nghị định số \d+/\d{4}/NĐ-CP',
    ]
    
    citations = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        citations.extend(matches)
    
    if not citations:
        return "No legal citations found in the provided text."
    
    # Remove duplicates while preserving order
    seen = set()
    unique_citations = []
    for c in citations:
        if c not in seen:
            seen.add(c)
            unique_citations.append(c)
    
    statuses = validate_citations(unique_citations)
    return format_validation_report(statuses)


if __name__ == "__main__":
    # Test the module
    test_citations = [
        "Law No. 60/2010/QH12 on Minerals",
        "Decree No. 15/2012/ND-CP",
        "Law No. 47/2005/QH11",  # This one is superseded
        "Circular No. 38/2015/TT-BTNMT",
    ]
    
    print("Testing citation validation...")
    statuses = validate_citations(test_citations)
    print(format_validation_report(statuses))
