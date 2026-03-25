# 🏦 Bank of Africa — Complete Agentic AI Banking System

**FintechNGR x CloudPlexo Workshop — March 26, 2026**

A full AI-powered digital banking system where a Supervisor Agent orchestrates three specialized sub-agents to handle real banking operations through natural language conversation. Built entirely on AWS.

---

## 🗂️ What's in This Package

This is the **single, complete package** containing everything needed to run the Bank of Africa workshop. Nothing is missing.

```
bank-of-africa-final/
│
├── README.md                ← YOU ARE HERE — master guide
├── CLAUDE.md                ← Context file for Claude Code / Claude terminal continuation
├── SETUP_GUIDE.md           ← Detailed 10-step manual deployment guide
│
├── cfn/                     ← OPTION A: CloudFormation / SAM template
│   └── template.yaml           One-stack deployment of all AWS resources
│
├── cdk/                     ← OPTION B: AWS CDK (Python) deployment
│   ├── app.py                   CDK app entry point
│   ├── cdk.json                 CDK config
│   ├── requirements.txt         CDK Python dependencies
│   └── stacks/
│       └── boa_stack.py         Complete CDK stack (same resources as CFN)
│
├── lambda_code/             ← All Lambda function source code
│   ├── seed/                    Auto-seeds DynamoDB on deploy (CloudFormation Custom Resource)
│   │   ├── seed_handler.py      5 Nigerian customers, 13 accounts, ~1000 transactions
│   │   └── cfnresponse.py       CloudFormation response helper
│   ├── api/                     API Gateway → Bedrock bridge
│   │   └── api_handler.py       Bedrock Converse API with tool use (agentic loop)
│   └── agent_code/              Bedrock Agent action group Lambdas (6 functions)
│       ├── get_user_profile.py
│       ├── list_accounts.py
│       ├── get_balance.py
│       ├── get_recent_transactions.py
│       ├── transfer_funds.py
│       └── deposit_withdraw.py
│
├── agentcore/               ← PRODUCTION VERSION: Strands SDK + AgentCore Runtime
│   ├── agent/
│   │   ├── agent.py             Supervisor + 3 sub-agents + Swarm + AgentCore entrypoint
│   │   ├── api_handler.py       AgentCore-specific API bridge
│   │   └── requirements.txt     strands-agents, bedrock-agentcore, boto3
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── account_tools.py     @tool: get_user_profile, list_accounts, get_balance
│   │   ├── transaction_tools.py @tool: transfer_funds, deposit_withdraw, get_recent_transactions
│   │   └── knowledge_tools.py   @tool: search_bank_handbook (Bedrock Knowledge Base)
│   └── deploy.sh               AgentCore deployment script
│
├── frontend/                ← React 18 chat application
│   ├── package.json
│   ├── public/
│   │   └── index.html
│   └── src/
│       ├── index.js
│       ├── App.jsx              Main component: state, session, message handling
│       ├── components/
│       │   ├── ChatInterface.jsx    Message list, typing indicator, input area
│       │   ├── MessageBubble.jsx    User/assistant bubbles with NGN highlighting
│       │   ├── Sidebar.jsx          Agent status, 8 suggested prompts, controls
│       │   └── AgentTrace.jsx       Agent reasoning timeline (toggle panel)
│       ├── styles/
│       │   └── app.css              Dark fintech theme (DM Sans + JetBrains Mono)
│       └── utils/
│           └── api.js               API client, session management, suggested prompts
│
├── data/
│   └── seed_data.py         ← Standalone seed script (for local dev without CloudFormation)
│
├── docs/
│   ├── PARTICIPANT_GUIDE.md ← Step-by-step guide participants follow during the 1-hour workshop
│   └── bank_handbook.md     ← Bank of Africa Customer Handbook (source for Bedrock Knowledge Base)
│
└── scripts/
    ├── deploy.sh            ← ONE-CLICK deploy for AWS CloudShell
    └── cleanup.sh           ← ONE-CLICK teardown after workshop
```

---

## 🚀 Three Ways to Deploy

### Option 1: One-Click (Workshop — participants use this)
```bash
# In AWS CloudShell:
chmod +x scripts/deploy.sh && ./scripts/deploy.sh
```
Deploys everything in ~10 minutes. Outputs a Chat App URL.

### Option 2: CloudFormation / SAM
```bash
cd cfn
sam validate      # Check template syntax
sam build         # Build with Docker (configured in samconfig.toml)
sam deploy        # Deploy using saved config
```

**For development (faster iterations):**
```bash
sam sync --stack-name bank-of-africa          # One-time sync
sam sync --stack-name bank-of-africa --watch  # Auto-sync on file changes
```

### Option 3: AWS CDK
```bash
cd cdk
pip install -r requirements.txt
cdk bootstrap
cdk deploy
```

All three options deploy the same resources.

---

## 💻 Run Frontend Locally

After deploying the backend (any option above), run the React chat app:

```bash
cd frontend
npm install
npm start
```

Then update `frontend/src/utils/api.js` line 7 with your API Gateway URL from the deployment output.

The app opens at `http://localhost:3000`.

---

## 🏗️ Architecture

```
[React Chat UI] → [API Gateway] → [Lambda: api_handler.py]
                                         │
                         Bedrock Converse API (agentic loop)
                         Model: Claude Sonnet 4
                                         │
                        ┌────────────────┼────────────────┐
                        ▼                ▼                ▼
                  get_user_profile  transfer_funds   search_handbook
                  list_accounts    deposit_withdraw  (Bedrock KB)
                  get_balance      get_transactions
                        │                │
                        ▼                ▼
                    DynamoDB          DynamoDB
                   boa_users        boa_transactions
                   boa_accounts
```

**Workshop version:** Uses Bedrock Converse API with tool use (deploys via CloudFormation, works immediately).

**Production version** (in `agentcore/`): Same logic using Strands Agents SDK + AgentCore Runtime with MicroVM isolation, Swarm pattern orchestration, and OpenTelemetry observability.

---

## 📋 Workshop 1-Hour Schedule

| Time | Activity |
|------|----------|
| 0:00-0:10 | **Deploy** — One command in CloudShell, wait ~8 min |
| 0:10-0:15 | **First query** — Open Chat App, try "Show me the profile for user 2" |
| 0:15-0:35 | **6 guided challenges** — Balances, transfers, insufficient funds, RAG, multi-step |
| 0:35-0:45 | **Free experimentation** — Edge cases, different users, breaking things |
| 0:45-0:55 | **Under the hood** — Facilitator shows agent reasoning + eKYC demo + AgentCore |
| 0:55-1:00 | **Q&A + wrap-up** |

See `docs/PARTICIPANT_GUIDE.md` for the full step-by-step guide participants follow.

---

## 📄 Documentation Index

| File | Purpose | Who Reads It |
|------|---------|-------------|
| `README.md` | Master guide (this file) | Everyone |
| `CLAUDE.md` | Full project context for Claude Code continuation | Developers using Claude |
| `SETUP_GUIDE.md` | Detailed 10-step manual deployment | CloudPlexo engineering team |
| `docs/PARTICIPANT_GUIDE.md` | Workshop participant step-by-step | Workshop attendees |
| `docs/bank_handbook.md` | Bank product handbook (Knowledge Base source) | Bedrock KB / Reference |

---

## 🧹 Cleanup

```bash
chmod +x scripts/cleanup.sh && ./scripts/cleanup.sh
```

---

## 🔑 AWS Services Used

| Service | Purpose |
|---------|---------|
| Amazon Bedrock (Claude Sonnet 4) | AI reasoning, tool calling, response generation |
| Amazon DynamoDB | Customer profiles, accounts, transactions (3 tables) |
| AWS Lambda (Python 3.12) | 8 functions: seed, API handler, 6 banking tools |
| Amazon API Gateway | REST API with CORS for React frontend |
| Amazon S3 | Bank handbook storage + frontend hosting |
| Bedrock Knowledge Bases | RAG for bank policy questions (optional setup) |
| AWS CloudFormation / CDK | Infrastructure-as-code deployment |
| Bedrock AgentCore (production) | MicroVM runtime for Strands SDK agents |
