"""
Bank of Africa — Knowledge Base Tool
Strands Agent tool that queries the Bedrock Knowledge Base for bank policy information.
"""

import os
import boto3
from strands import tool

bedrock_agent_runtime = boto3.client("bedrock-agent-runtime")
KNOWLEDGE_BASE_ID = os.environ.get("KNOWLEDGE_BASE_ID", "YOUR_KB_ID")


@tool
def search_bank_handbook(query: str) -> str:
    """
    Search the Bank of Africa Customer Handbook for policy information.
    Use this for questions about fees, interest rates, account types,
    transaction limits, KYC tiers, dispute resolution, and bank procedures.

    Args:
        query: The question or topic to search for (e.g., "international transfer fees",
               "savings account interest rate", "KYC tier 2 requirements")

    Returns:
        Relevant information from the bank handbook with source citations.
    """
    try:
        response = bedrock_agent_runtime.retrieve(
            knowledgeBaseId=KNOWLEDGE_BASE_ID,
            retrievalQuery={"text": query},
            retrievalConfiguration={
                "vectorSearchConfiguration": {
                    "numberOfResults": 5,
                }
            },
        )

        results = response.get("retrievalResults", [])

        if not results:
            return (
                "I couldn't find specific information about that in our handbook. "
                "Please contact Bank of Africa customer service at +234 1 234 5678 "
                "or visit your nearest branch for assistance."
            )

        # Compile results
        lines = ["From the Bank of Africa Customer Handbook:\n"]
        for i, result in enumerate(results, 1):
            content = result.get("content", {}).get("text", "")
            score = result.get("score", 0)
            if content and score > 0.3:  # Relevance threshold
                # Trim to reasonable length
                if len(content) > 500:
                    content = content[:500] + "..."
                lines.append(f"[Section {i}] {content}\n")

        if len(lines) == 1:
            return (
                "I found some references but they don't seem directly relevant. "
                "Please contact customer service at +234 1 234 5678 for specific guidance."
            )

        return "\n".join(lines)

    except Exception as e:
        return (
            f"I'm having trouble accessing the handbook right now. "
            f"Please contact customer service at +234 1 234 5678."
        )
