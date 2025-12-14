"""
Evaluation Runner for Legal Research System

This script runs the benchmark questions through the research system
and generates an evaluation report.
"""
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv, find_dotenv
from src.config import get_model_client
from src.agents.planner import create_planner_agent
from src.agents.retriever import create_retriever_agent
from src.agents.analyzer import create_analyzer_agent
from src.agents.critic import create_critic_agent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination

logging.basicConfig(level=logging.WARNING)  # Reduce noise during evaluation


def load_benchmark_questions(filepath: str = "tests/benchmark_questions.json") -> Dict[str, Any]:
    """Load benchmark questions from JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


async def run_single_query(query: str, model_client, max_messages: int = 8) -> Dict[str, Any]:
    """Run a single query through the research system."""
    planner = create_planner_agent(model_client)
    retriever = create_retriever_agent(model_client)
    analyzer = create_analyzer_agent(model_client)
    critic = create_critic_agent(model_client)
    
    termination = TextMentionTermination("APPROVE") | MaxMessageTermination(max_messages=max_messages)
    
    team = RoundRobinGroupChat(
        participants=[planner, retriever, analyzer, critic],
        termination_condition=termination,
    )
    
    task = f"Legal Query: {query}\nPlease plan and execute the research."
    
    messages = []
    try:
        async for event in team.run_stream(task=task):
            # Collect messages
            if hasattr(event, 'content'):
                messages.append({
                    "source": getattr(event, 'source', 'unknown'),
                    "content": str(event.content)[:500]  # Truncate for storage
                })
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "messages": messages
        }
    
    return {
        "success": True,
        "messages": messages,
        "message_count": len(messages)
    }


def check_references(result: Dict, expected_refs: List[str]) -> Dict[str, Any]:
    """Check if expected references appear in the output."""
    all_content = " ".join([m.get("content", "") for m in result.get("messages", [])])
    
    found = []
    missing = []
    
    for ref in expected_refs:
        if ref in all_content:
            found.append(ref)
        else:
            missing.append(ref)
    
    return {
        "found_references": found,
        "missing_references": missing,
        "reference_score": len(found) / len(expected_refs) if expected_refs else 1.0
    }


def generate_report(results: List[Dict], benchmark: Dict) -> str:
    """Generate a markdown evaluation report."""
    lines = [
        "# Legal Research System Evaluation Report",
        f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Benchmark Version:** {benchmark.get('benchmark_version', 'N/A')}",
        f"**Questions Evaluated:** {len(results)}",
        "",
        "## Summary",
        "",
    ]
    
    successful = sum(1 for r in results if r.get("success"))
    total_ref_score = sum(r.get("reference_check", {}).get("reference_score", 0) for r in results)
    avg_ref_score = total_ref_score / len(results) if results else 0
    
    lines.extend([
        f"- **Success Rate:** {successful}/{len(results)} ({100*successful/len(results):.0f}%)",
        f"- **Avg Reference Score:** {avg_ref_score:.2%}",
        "",
        "## Detailed Results",
        "",
    ])
    
    for r in results:
        q = r.get("question", {})
        lines.extend([
            f"### {q.get('id', 'Unknown')}: {q.get('category', 'N/A')}",
            f"**Query:** {q.get('query', 'N/A')}",
            f"**Difficulty:** {q.get('difficulty', 'N/A')}",
            "",
        ])
        
        if r.get("success"):
            ref_check = r.get("reference_check", {})
            lines.extend([
                f"- ✅ Completed with {r.get('message_count', 0)} messages",
                f"- **Reference Score:** {ref_check.get('reference_score', 0):.0%}",
                f"- **Found:** {', '.join(ref_check.get('found_references', [])) or 'None'}",
                f"- **Missing:** {', '.join(ref_check.get('missing_references', [])) or 'None'}",
            ])
        else:
            lines.extend([
                f"- ❌ Failed: {r.get('error', 'Unknown error')}",
            ])
        
        lines.append("")
    
    return "\n".join(lines)


async def run_evaluation(question_ids: List[str] = None, max_questions: int = 3):
    """
    Run evaluation on benchmark questions.
    
    Args:
        question_ids: Specific question IDs to run (e.g., ["Q001", "Q002"])
        max_questions: Maximum number of questions to evaluate
    """
    load_dotenv(find_dotenv(), override=True)
    
    print("Loading benchmark questions...")
    benchmark = load_benchmark_questions()
    questions = benchmark.get("questions", [])
    
    # Filter by IDs if specified
    if question_ids:
        questions = [q for q in questions if q.get("id") in question_ids]
    
    # Limit number of questions
    questions = questions[:max_questions]
    
    print(f"Running evaluation on {len(questions)} questions...")
    
    try:
        model_client = get_model_client()
    except Exception as e:
        print(f"Failed to initialize model client: {e}")
        return
    
    results = []
    
    for i, question in enumerate(questions, 1):
        print(f"\n[{i}/{len(questions)}] Evaluating: {question.get('id')} - {question.get('category')}")
        print(f"  Query: {question.get('query')[:50]}...")
        
        result = await run_single_query(question.get("query", ""), model_client)
        result["question"] = question
        
        # Check references
        if result.get("success"):
            result["reference_check"] = check_references(
                result, 
                question.get("expected_references", [])
            )
            print(f"  ✅ Success - Ref Score: {result['reference_check']['reference_score']:.0%}")
        else:
            print(f"  ❌ Failed: {result.get('error', 'Unknown')[:50]}")
        
        results.append(result)
        
        # Small delay to avoid rate limiting
        await asyncio.sleep(2)
    
    # Generate report
    print("\nGenerating evaluation report...")
    report = generate_report(results, benchmark)
    
    report_path = Path("tests/evaluation_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\nReport saved to: {report_path}")
    print("\n" + "="*50)
    print(report)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run legal research system evaluation")
    parser.add_argument("--questions", "-q", nargs="+", help="Specific question IDs to evaluate")
    parser.add_argument("--max", "-m", type=int, default=3, help="Maximum questions to evaluate")
    
    args = parser.parse_args()
    
    asyncio.run(run_evaluation(
        question_ids=args.questions,
        max_questions=args.max
    ))
