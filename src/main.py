import asyncio
import logging
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from src.config import get_model_client
from src.agents.planner import create_planner_agent
from src.agents.retriever import create_retriever_agent
from src.agents.analyzer import create_analyzer_agent
from src.agents.critic import create_critic_agent
from src.agents.synthesizer import create_synthesizer_agent
from dotenv import load_dotenv, find_dotenv

# Configure logging to suppress noisy output if needed, or see debug info
logging.basicConfig(level=logging.INFO)

async def main():
    load_dotenv(find_dotenv(), override=True)
    
    print("--- Initializing MS AutoGen Agents ---")
    
    # Create the shared model client
    try:
        model_client = get_model_client()
    except Exception as e:
        print(f"Error initializing model client: {e}")
        return

    planner = create_planner_agent(model_client)
    retriever = create_retriever_agent(model_client)
    analyzer = create_analyzer_agent(model_client)
    critic = create_critic_agent(model_client)
    synthesizer = create_synthesizer_agent(model_client)
    
    # === PHASE 1: Research & Critique ===
    # Termination: "APPROVE" from Critic or max messages
    research_termination = TextMentionTermination("APPROVE") | MaxMessageTermination(max_messages=12)
    
    print("Creating Research Team (Planner -> Retriever -> Analyzer -> Critic)...")
    research_team = RoundRobinGroupChat(
        participants=[planner, retriever, analyzer, critic],
        termination_condition=research_termination,
    )

    print("\n--- System Ready ---")
    # query = input("Enter your legal query: ")
    # if not query:
    #     query = "Quy định về thu hồi đất"
    query = "Khoáng sản nhóm III"  # Hardcoded for testing
    
    task = f"Legal Query: {query}\nPlease plan and execute the research."
    
    print(f"Starting research task: {task}\n")
    
    # Run Phase 1: Research
    research_result = await Console(research_team.run_stream(task=task))
    
    # === PHASE 2: Synthesis ===
    # After approval, synthesize the final document
    print("\n--- Research Approved. Starting Synthesis Phase ---\n")
    
    synthesis_termination = MaxMessageTermination(max_messages=2)
    
    synthesis_team = RoundRobinGroupChat(
        participants=[synthesizer],
        termination_condition=synthesis_termination,
    )
    
    # Pass context from research to synthesizer
    synthesis_task = f"""Based on the approved research above, produce the final legal research document.

Original Query: {query}

Please synthesize a comprehensive, well-formatted legal brief with proper citations."""
    
    await Console(synthesis_team.run_stream(task=synthesis_task))
    
    print("\n--- Legal Research Complete ---")

if __name__ == "__main__":
    asyncio.run(main())
