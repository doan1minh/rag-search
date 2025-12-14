from typing import List, Optional
try:
    from autogen import AssistantAgent
except ImportError:
    try:
        from autogen_agentchat.agents import AssistantAgent
    except ImportError:
         print("CRITICAL: Could not import Agent classes from autogen or autogen_agentchat")
         raise
from src.config import get_model_client

def create_synthesizer_agent(model_client=None) -> AssistantAgent:
    """
    Creates the Synthesizer agent which produces the final, polished legal research output.
    
    This agent takes the approved analysis from the Critic and formats it into
    a professional legal document with proper citations.
    """
    if model_client is None:
        model_client = get_model_client()

    PROMPT_TEMPLATE = """You are a LEGAL DOCUMENT SYNTHESIZER for a Vietnamese legal research system.

**Your Role:**
After the research has been approved by the Critic, you produce the FINAL OUTPUT document.

**Your Task:**
Transform the approved research into a polished, professional legal brief that:

1. **Structure**: Use clear headings and sections:
   - Executive Summary (1-2 paragraphs)
   - Legal Framework (relevant laws and regulations)
   - Analysis (detailed discussion)
   - Conclusion & Recommendations

2. **Citations**: Format all legal references properly:
   - Vietnamese format: "Điều X, Luật số Y/YEAR/QH" 
   - English format: "Article X, Law No. Y/YEAR/QH"
   - Include document dates when available

3. **Language**: 
   - Professional, objective tone
   - Clear and concise explanations
   - Avoid speculation; only state what the evidence supports

4. **Quality**:
   - No hallucinated citations
   - All claims must be traceable to retrieved evidence
   - Highlight any areas where legal interpretation may vary

**Output Format:**
Produce a complete, ready-to-use legal research document in Markdown format.
"""

    agent = AssistantAgent(
        name="Synthesizer_Agent",
        model_client=model_client,
        system_message=PROMPT_TEMPLATE,
    )
    return agent
