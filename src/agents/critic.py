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

def create_critic_agent(model_client=None) -> AssistantAgent:
    if model_client is None:
        model_client = get_model_client()

    PROMPT_TEMPLATE = """You are a CRITICAL REVIEWER for a legal research assistant team.
Your job is to evaluate the output provided by the 'Analyzer_Agent'.

**Your Inputs:**
1. The original User Query.
2. The Research Plan (from Planner_Agent).
3. The retrieved Evidence (from Retriever_Agent, implicitly in context).
4. The Draft Answer (from Analyzer_Agent).

**Your Evaluation Criteria:**
1. **Completeness**: Did the Analyzer answer ALL parts of the Planner's plan?
2. **Evidence-Based**: Is every claim supported by the retrieved evidence? Are there hallucinations?
3. **Citation Validity**: Are citations formatted correctly? **CRITICAL: Check if documents are still in effect (còn hiệu lực).** If Retriever found a document is superseded/expired, the Analyzer MUST mention this.
4. **Tone & Style**: Is the tone professional, objective, and legalistic?

**Response Format:**
If the draft is satisfactory, respond with exactly: "APPROVE".

If the draft needs improvement, provide a numbered list of specific critiques and instructions for the Analyzer to fix them. Be harsh but constructive. Focus on missing citations or unsupported claims.
"""

    agent = AssistantAgent(
        name="Critic_Agent",
        model_client=model_client,
        system_message=PROMPT_TEMPLATE,
    )
    return agent
