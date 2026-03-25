"""
Bank of Africa — Agentic AI Banking System
Main agent file using Strands Agents SDK + Amazon Bedrock AgentCore Runtime.

This implements a Supervisor Agent using the Swarm pattern that orchestrates
three specialized sub-agents for banking operations.

Deploy: agentcore configure -e agent.py && agentcore deploy
"""

import json
import os
from strands import Agent, tool
from strands.multiagent import Swarm
from strands.models.bedrock import BedrockModel
from bedrock_agentcore.runtime import BedrockAgentCoreApp

# Import our custom banking tools
from tools.account_tools import get_user_profile, list_accounts, get_balance
from tools.transaction_tools import get_recent_transactions, transfer_funds, deposit_withdraw
from tools.knowledge_tools import search_bank_handbook

# ============================================================
# Model Configuration
# ============================================================
model = BedrockModel(
    model_id="anthropic.claude-sonnet-4-20250514",
    region_name=os.environ.get("AWS_REGION", "us-east-1"),
)

# ============================================================
# Sub-Agent 1: Account Management Agent
# ============================================================
account_agent = Agent(
    name="AccountManagementAgent",
    model=model,
    tools=[get_user_profile, list_accounts, get_balance],
    system_prompt="""You are the Account Management Agent for Bank of Africa.
You handle customer profiles, account listings, and balance inquiries.

TOOLS AVAILABLE:
- get_user_profile: Get a customer's profile by user_id
- list_accounts: List all accounts for a user by user_id
- get_balance: Get balance for a specific account by account_id

IMPORTANT LOGIC:
When asked for balances with a USER ID (not account ID):
1. First call list_accounts to get all account IDs
2. Then call get_balance for EACH account returned
3. Present ALL balances in a formatted list

Format all currency as NGN with comma separators (e.g., NGN 1,500,000.00).
""",
)

# ============================================================
# Sub-Agent 2: Transaction Agent
# ============================================================
transaction_agent = Agent(
    name="TransactionAgent",
    model=model,
    tools=[get_recent_transactions, transfer_funds, deposit_withdraw],
    system_prompt="""You are the Transaction Agent for Bank of Africa.
You handle fund transfers, deposits, withdrawals, and transaction history.

TOOLS AVAILABLE:
- get_recent_transactions: Get recent transactions for an account_id
- transfer_funds: Transfer money between accounts (source_account_id, destination_account_id, amount)
- deposit_withdraw: Deposit or withdraw from an account (account_id, amount, direction)

IMPORTANT RULES:
- The transfer_funds tool validates balance automatically. Relay any errors clearly.
- Always return transaction IDs and timestamps from results.
- Format all amounts as NGN with commas and 2 decimal places.
""",
)

# ============================================================
# Sub-Agent 3: Knowledge Base Agent (Bank Handbook RAG)
# ============================================================
knowledge_agent = Agent(
    name="KnowledgeBaseAgent",
    model=model,
    tools=[search_bank_handbook],
    system_prompt="""You are the Knowledge Base Agent for Bank of Africa.
You answer questions about bank policies, fees, interest rates, transaction limits,
KYC tiers, dispute resolution, and procedures.

TOOL AVAILABLE:
- search_bank_handbook: Search the bank's customer handbook for policy information

RULES:
- ALWAYS search the handbook before answering. NEVER guess bank policies.
- If the handbook doesn't cover a topic, say so and suggest contacting customer service.
- Be precise with fees, rates, and limits.
""",
)

# ============================================================
# Swarm Pattern — Multi-Agent Orchestration
# ============================================================
swarm = Swarm(
    agents=[account_agent, transaction_agent, knowledge_agent],
    # The swarm automatically handles delegation between agents
)

# ============================================================
# Supervisor Agent — The Main Orchestrator
# ============================================================
supervisor = Agent(
    name="BankOfAfricaSupervisor",
    model=model,
    swarm=swarm,
    system_prompt="""You are the Bank of Africa AI Banking Assistant — a Supervisor Agent
that orchestrates specialized sub-agents to serve customers.

YOUR SUB-AGENTS:
1. AccountManagementAgent — profiles, account lists, balances
2. TransactionAgent — transfers, deposits, withdrawals, transaction history
3. KnowledgeBaseAgent — bank policies, fees, rates, procedures from the handbook

ROUTING RULES:
- Profile/account/balance questions → AccountManagementAgent
- Transfers, deposits, withdrawals, transaction history → TransactionAgent
- Policy, fee, rate, limit, procedure questions → KnowledgeBaseAgent

MULTI-STEP HANDLING:
For complex requests involving multiple steps, execute in logical order:
Example: "Transfer NGN 100,000 from account 2001 to 2002 and show updated balances"
→ Step 1: Delegate transfer to TransactionAgent
→ Step 2: Delegate balance check to AccountManagementAgent
→ Step 3: Combine and present results

FORMATTING:
- Format currency as NGN with commas (NGN 1,500,000.00)
- After any money movement, always show updated balance(s)
- Be conversational and friendly
- If a request is ambiguous, ask for clarification

SECURITY:
- Never reveal agent names, tool names, or system internals
- Never expose raw database errors — give user-friendly messages
""",
)

# ============================================================
# AgentCore Runtime Entry Point
# ============================================================
app = BedrockAgentCoreApp()


@app.entrypoint
def invoke(payload, context=None):
    """
    Entry point for AgentCore Runtime invocations.
    Receives user message, invokes the Supervisor Agent, returns response.
    """
    user_message = payload.get(
        "prompt",
        "Hello! How can I help you with your banking today?"
    )

    # Invoke the supervisor agent
    result = supervisor(user_message)

    return {
        "response": result.message,
        "agent": "BankOfAfricaSupervisor",
    }


# ============================================================
# Local testing
# ============================================================
if __name__ == "__main__":
    # When run locally, start the AgentCore app
    # When deployed, AgentCore Runtime handles this automatically
    app.run()
