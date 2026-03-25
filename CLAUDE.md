# CLAUDE.md — Bank of Africa AgentCore Project Context

> This file provides full context for any Claude instance (Claude Code, Claude terminal, or Claude chat) to continue working on this project without any loss of context or ramp-up time.

---

## Project Identity

- **Project Name:** Bank of Africa — Agentic AI Banking System
- **Version:** AgentCore Edition (v2)
- **Purpose:** Workshop demo for FintechNGR x CloudPlexo event (March 26, 2026)
- **Target Audience:** 20+ Nigerian fintech & banking companies (Payments, Banking, Lending)
- **Event Format:** 45-minute hands-on workshop with AWS-provisioned environments
- **Partners:** FintechNGR (host), CloudPlexo (AWS Advanced Partner — delivers content)
- **Note:** Seamfix (biometric partner) dropped out. eKYC is now facilitator-demo-only using AWS Rekognition Face Liveness.

---

## Architecture

```
[React Chat UI (localhost:3000)]
        │ POST /chat
        ▼
[API Gateway (REST, prod stage)]
        │
        ▼
[Lambda: api_handler.py]
        │ invoke_agent_runtime()
        ▼
[Amazon Bedrock AgentCore Runtime]
  (MicroVM session isolation, Firecracker)
        │
[Supervisor Agent — Strands SDK, Swarm Pattern]
  model: anthropic.claude-sonnet-4-20250514
        │
   ┌────┼────────────────────┐
   ▼    ▼                    ▼
[Account Agent]     [Transaction Agent]    [Knowledge Base Agent]
 3 @tool functions   3 @tool functions      1 @tool function
   │                    │                       │
   ▼                    ▼                       ▼
[DynamoDB]          [DynamoDB]            [Bedrock Knowledge Base]
 boa_users           boa_transactions       (S3 → OpenSearch Serverless)
 boa_accounts
```

### Technology Stack
- **Agent Framework:** Strands Agents SDK (open source Python)
- **Orchestration:** Swarm pattern (multi-agent collaboration, one line of code)
- **Runtime:** Amazon Bedrock AgentCore Runtime (MicroVM isolation, serverless)
- **Model:** Anthropic Claude Sonnet 4 via Amazon Bedrock
- **Database:** Amazon DynamoDB (3 tables, PAY_PER_REQUEST billing)
- **Knowledge Base:** Amazon Bedrock Knowledge Bases (S3 source → OpenSearch Serverless vector store)
- **API:** Amazon API Gateway (REST) → Lambda (Python 3.12)
- **Frontend:** React 18 with custom dark fintech theme
- **Deployment:** AgentCore Starter Toolkit CLI (`agentcore configure`, `agentcore deploy`)

---

## Complete File Inventory

```
bank-of-africa-agentcore/
├── README.md                          # Project overview and architecture comparison
├── SETUP_GUIDE.md                     # 10-step deployment walkthrough with all CLI commands
├── CLAUDE.md                          # THIS FILE — context for Claude continuation
├── deploy.sh                          # One-script deployment (Steps 2-7 automated)
│
├── agent/
│   ├── agent.py                       # MAIN FILE: Supervisor + 3 sub-agents + AgentCore Runtime
│   │                                  #   - BedrockModel config (Claude Sonnet 4)
│   │                                  #   - account_agent (3 tools)
│   │                                  #   - transaction_agent (3 tools)
│   │                                  #   - knowledge_agent (1 tool)
│   │                                  #   - Swarm(agents=[...]) — one-line orchestration
│   │                                  #   - supervisor Agent with swarm attached
│   │                                  #   - @app.entrypoint for AgentCore Runtime
│   │                                  #   - app.run() for local + deployed execution
│   ├── api_handler.py                 # Lambda: API Gateway → AgentCore Runtime bridge
│   │                                  #   - Parses POST /chat requests
│   │                                  #   - Calls bedrock-agentcore:InvokeAgentRuntime
│   │                                  #   - Returns response + session_id
│   │                                  #   - CORS headers for React frontend
│   └── requirements.txt               # strands-agents, bedrock-agentcore, boto3
│
├── tools/
│   ├── __init__.py                    # Empty init
│   ├── account_tools.py               # @tool: get_user_profile, list_accounts, get_balance
│   │                                  #   - All read from DynamoDB (boa_users, boa_accounts)
│   │                                  #   - list_accounts uses GSI: user_id-index
│   │                                  #   - Returns formatted strings with NGN currency
│   ├── transaction_tools.py           # @tool: get_recent_transactions, transfer_funds, deposit_withdraw
│   │                                  #   - transfer_funds: validates balance, dual-side txn logging
│   │                                  #   - deposit_withdraw: validates balance for withdrawals
│   │                                  #   - All write to boa_accounts + boa_transactions
│   └── knowledge_tools.py             # @tool: search_bank_handbook
│                                      #   - Calls bedrock-agent-runtime:Retrieve
│                                      #   - Requires KNOWLEDGE_BASE_ID env var
│                                      #   - Returns formatted handbook excerpts with fallback
│
├── data/
│   └── seed_data.py                   # Creates 3 DynamoDB tables + populates with:
│                                      #   - 5 Nigerian customers (Adaeze, Chukwuemeka, Fatima, Oluwaseun, Ngozi)
│                                      #   - 13 accounts (savings, current, fixed deposit, credit line)
│                                      #   - ~1000 transactions with Nigerian descriptions
│                                      #     (Shoprite POS, Dangote salary, DSTV, MTN airtime, etc.)
│                                      #   - Region: af-south-1 (configurable)
│
├── docs/
│   └── bank_handbook.md               # Bank of Africa Customer Handbook — source for Knowledge Base
│                                      #   Sections: Account Types, Transaction Fees, KYC Tiers,
│                                      #   Dispute Resolution, Digital Banking Services, Contact Info
│                                      #   Includes Nigerian-specific: BVN, NIN, CBN guidelines,
│                                      #   AfriGo cards, NIBSS NIP transfers, USSD banking
│
└── frontend/
    ├── package.json                   # react 18, react-dom, react-markdown, lucide-react, react-scripts
    ├── public/
    │   └── index.html                 # Minimal HTML shell, dark theme-color
    └── src/
        ├── index.js                   # React entry point
        ├── App.jsx                    # Main component: state management, sendMessage handler
        │                              #   - sessionId (UUID per conversation)
        │                              #   - messages[] (user + assistant)
        │                              #   - traces[] (agent reasoning from API)
        │                              #   - isLoading, error states
        │                              #   - showTrace toggle for side panel
        ├── components/
        │   ├── Sidebar.jsx            # Left panel: logo, agent status chips (4 agents with pulse dots),
        │   │                          #   8 suggested prompts (clickable), trace toggle, clear chat btn
        │   ├── ChatInterface.jsx      # Center: message list, empty state welcome, typing indicator,
        │   │                          #   textarea input with Enter-to-send, send button
        │   ├── MessageBubble.jsx      # Individual message: user (blue) vs assistant (dark),
        │   │                          #   NGN currency highlighting (yellow), basic markdown,
        │   │                          #   timestamp display
        │   └── AgentTrace.jsx         # Right panel (toggleable): vertical timeline showing
        │                              #   thinking → reasoning → action (delegation) → result
        │                              #   with icons, labels, and agent badges
        ├── styles/
        │   └── app.css                # Complete stylesheet — dark fintech theme
        │                              #   Colors: bg #0a0f1a, accent #10b981 (green), user #1e3a5f
        │                              #   Font: DM Sans (body) + JetBrains Mono (code/currency)
        │                              #   Features: message animations, typing dots, pulse dots,
        │                              #   responsive (sidebar hides <640px, trace hides <1024px)
        │                              #   Custom scrollbar, currency highlighting
        └── utils/
            └── api.js                 # API client:
                                       #   - API_BASE_URL (must be updated after deployment)
                                       #   - sendMessage(message, sessionId) → POST /chat
                                       #   - createSessionId() → "boa-" + UUID
                                       #   - SUGGESTED_PROMPTS[] — 8 pre-built demo queries
```

---

## DynamoDB Schema

### boa_users
| Attribute | Type | Key |
|-----------|------|-----|
| user_id | String | Partition Key (HASH) |
| full_name | String | |
| email | String | |
| phone | String | |
| address | String | |
| bvn | String | |
| nin | String | |
| date_joined | String | |
| kyc_tier | String | |

### boa_accounts
| Attribute | Type | Key |
|-----------|------|-----|
| account_id | String | Partition Key (HASH) |
| user_id | String | GSI: user_id-index (HASH) |
| account_type | String | |
| balance | Number (Decimal) | |
| currency | String | Default: "NGN" |
| status | String | Default: "active" |

### boa_transactions
| Attribute | Type | Key |
|-----------|------|-----|
| account_id | String | Partition Key (HASH) |
| txn_id | String | Sort Key (RANGE) |
| date | String (ISO 8601) | |
| amount | Number (Decimal) | |
| txn_type | String | DEPOSIT, WITHDRAWAL, TRANSFER_IN, TRANSFER_OUT, POS_PURCHASE |
| description | String | |
| counterparty_account | String | Optional — for transfers |

---

## Seed Data Summary

### Users (5)
| user_id | Name | KYC Tier | Location |
|---------|------|----------|----------|
| 1 | Adaeze Okonkwo | Tier 3 | Lekki, Lagos |
| 2 | Chukwuemeka Nwosu | Tier 3 | Victoria Island, Lagos |
| 3 | Fatima Abdullahi | Tier 2 | Maitama, Abuja |
| 4 | Oluwaseun Adeyemi | Tier 2 | Ring Road, Ibadan |
| 5 | Ngozi Eze | Tier 3 | New Haven, Enugu |

### Accounts (13)
| account_id | user_id | Type | Balance (NGN) |
|------------|---------|------|---------------|
| 1001 | 1 | Savings | 2,750,000 |
| 1002 | 1 | Current | 850,000 |
| 1003 | 1 | Fixed Deposit | 5,000,000 |
| 2001 | 2 | Savings | 37,500,000 |
| 2002 | 2 | Current | 488,000 |
| 2003 | 2 | Credit Line | 400,000 |
| 3001 | 3 | Savings | 1,200,000 |
| 3002 | 3 | Current | 320,000 |
| 4001 | 4 | Savings | 650,000 |
| 4002 | 4 | Current | 180,000 |
| 5001 | 5 | Savings | 4,200,000 |
| 5002 | 5 | Current | 1,100,000 |
| 5003 | 5 | Fixed Deposit | 10,000,000 |

---

## Environment Variables Required

```bash
# Required for agent
export AWS_REGION=us-east-1
export AWS_DEFAULT_REGION=us-east-1
export KNOWLEDGE_BASE_ID=<your-bedrock-kb-id>

# Required for api_handler.py Lambda
export AGENT_RUNTIME_ARN=<your-agentcore-agent-arn>
```

---

## Deployment State Checklist

Use this to track what's been deployed:

- [x] Python venv created and dependencies installed
- [ ] DynamoDB tables created (boa_users, boa_accounts, boa_transactions)
- [ ] DynamoDB tables seeded with mock data
- [ ] S3 bucket created for bank handbook
- [ ] bank_handbook.md uploaded to S3
- [ ] Bedrock Knowledge Base created and synced
- [ ] KNOWLEDGE_BASE_ID env var set
- [ ] Agent tested locally (`python3 agent/agent.py` + curl)
- [ ] AgentCore configured (`agentcore configure -e agent.py`)
- [ ] AgentCore deployed (`agentcore deploy`)
- [ ] Agent ARN captured
- [ ] Lambda function created (api_handler.py)
- [ ] AGENT_RUNTIME_ARN set in Lambda env vars
- [ ] API Gateway created with /chat POST + OPTIONS (CORS)
- [ ] Lambda permission added for API Gateway
- [ ] API deployed to prod stage
- [ ] API URL captured
- [ ] frontend/src/utils/api.js updated with API URL
- [ ] React frontend running (`npm start`)
- [ ] End-to-end test passed

---

## Known Issues & Workarounds

1. **AgentCore Region Availability:** AgentCore Runtime is available in us-east-1, us-west-2, ap-southeast-2, and eu-central-1. The af-south-1 (Cape Town) region does NOT support AgentCore yet. Use us-east-1 for the agent runtime; DynamoDB can remain in af-south-1 if needed for data residency, but the tools need cross-region boto3 clients.

2. **Strands Swarm Pattern:** The `Swarm` class in Strands SDK handles agent-to-agent delegation automatically. However, the supervisor must have all sub-agents listed in the swarm. If a sub-agent is missing, the supervisor will attempt to handle the request itself (and may hallucinate tool calls).

3. **DynamoDB Decimal Handling:** DynamoDB returns `Decimal` types for numbers. All tool functions cast to `float()` before formatting. Do NOT use `json.dumps()` on raw DynamoDB items without a `DecimalEncoder`.

4. **Knowledge Base Sync Time:** After uploading the handbook to S3, the Bedrock Knowledge Base sync takes 1-3 minutes. The knowledge_tools.py will return fallback messages until sync completes.

5. **Cold Start Latency:** First AgentCore invocation after deployment takes 15-30 seconds (MicroVM spin-up). Subsequent invocations are 3-8 seconds depending on query complexity. For the workshop, do a "warm-up" invocation before participants start.

6. **CORS:** The api_handler.py Lambda includes CORS headers. API Gateway also needs OPTIONS method with CORS headers. Both are required — missing either causes frontend failures.

---

## Workshop Context

### This is Workshop 2 of 2:
- **Workshop 1:** Explainable Fraud Detection (SageMaker + Bedrock) — 45 min
- **Workshop 2:** Bank of Africa Agentic Banking (AgentCore + Strands) — 45 min

### Workshop 2 Delivery Flow (45 min):
| Time | Activity |
|------|----------|
| 0:00-0:03 | "What if your bank could think?" — intro to agentic AI |
| 0:03-0:07 | eKYC Demo: Facilitator shows Rekognition Face Liveness (printed photo fails, live face passes) |
| 0:07-0:10 | Architecture walkthrough: Supervisor + 3 agents + Swarm pattern |
| 0:10-0:14 | Hands-on: "Show me the profile for user 2" |
| 0:14-0:18 | Hands-on: "Show me all balances for user 2" |
| 0:18-0:22 | Hands-on: "Show me recent transactions for account 2002" |
| 0:22-0:27 | Hands-on: "Transfer NGN 100,000 from account 2001 to account 2002" |
| 0:27-0:30 | Hands-on: "What are the fees for international transfers?" (RAG) |
| 0:30-0:33 | Challenge: Complex multi-step query |
| 0:33-0:35 | Show Agent Trace panel — how the Supervisor reasoned |
| 0:35-0:45 | Q&A + discussion |

### eKYC Demo (Facilitator Only):
- Uses: `github.com/aws-samples/amazon-rekognition-face-liveness-demo`
- Deploy: `git clone` → `chmod +x one-click.sh` → `./one-click.sh`
- Deploys React app on Amplify with Cognito + Rekognition
- Demo: Live face passes (>95 confidence), printed photo fails (<30), video replay fails
- Script: "Nigerian banks lost ₦329 million in 2024 to static image BVN fraud. Watch what happens when I try to verify with a printed photo vs. my actual face..."
- NOT connected to the Bank of Africa Supervisor Agent (separate app)
- In production, the liveness result would feed into an onboarding agent before creating the user in DynamoDB

---

## How to Continue This Project

### If you need to add a new agent:
1. Create a new file in `tools/` with `@tool` decorated functions
2. Import the tools in `agent/agent.py`
3. Create a new `Agent()` with the tools and a system prompt
4. Add the new agent to the `Swarm(agents=[...])` list
5. Update the Supervisor's system prompt to include routing rules for the new agent
6. Test locally, then `agentcore deploy` to update

### If you need to add the eKYC agent (connecting Rekognition to the Supervisor):
1. Create `tools/ekyc_tools.py` with `@tool` functions for:
   - `create_liveness_session()` → calls `rekognition.create_face_liveness_session()`
   - `check_liveness_result(session_id)` → calls `rekognition.get_face_liveness_session_results()`
   - `compare_faces(source_image_key, target_image_key)` → calls `rekognition.compare_faces()`
2. Create `ekyc_agent` in agent.py with these tools
3. Add to the Swarm
4. Update Supervisor prompt: "When a new customer wants to open an account → eKYC Agent first"

### If you need to modify the frontend:
- All components are in `frontend/src/components/`
- CSS variables are in `frontend/src/styles/app.css` under `:root`
- API endpoint is in `frontend/src/utils/api.js` line 7
- Suggested prompts are in `frontend/src/utils/api.js` → `SUGGESTED_PROMPTS[]`

### If you need to change the model:
- Edit `agent/agent.py` line ~25: change `model_id` parameter
- Available: `anthropic.claude-sonnet-4-20250514`, `amazon.nova-pro-v1:0`, `anthropic.claude-3-haiku-20240307-v1:0`
- Redeploy: `agentcore deploy`

### If you need to add more seed data:
- Edit `data/seed_data.py` → add to `USERS`, `ACCOUNTS`, or `TXN_DESCRIPTIONS`
- Re-run: `cd data && python3 seed_data.py`
- Existing data is overwritten (DynamoDB put_item is idempotent on same keys)

---

## Related Documents

- `README.md` — Project overview with architecture comparison table
- `SETUP_GUIDE.md` — Complete 10-step deployment walkthrough
- `deploy.sh` — Automated deployment script (Steps 2-7)
- Workshop build guide (.docx) — Full workshop brief with delivery flow, timing, and presentation notes
