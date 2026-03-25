# Bank of Africa — Complete Setup & Run Guide

Step-by-step instructions to deploy the Bank of Africa Agentic AI Banking System using Amazon Bedrock AgentCore + Strands Agents SDK.

---

## Prerequisites

Before starting, ensure you have:

| Requirement | How to Check | Install Link |
|-------------|-------------|--------------|
| AWS Account with Bedrock access | `aws sts get-caller-identity` | https://aws.amazon.com |
| AWS CLI v2 installed & configured | `aws --version` | https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html |
| Python 3.10 or newer | `python3 --version` | https://python.org/downloads |
| Node.js 18+ and npm | `node --version && npm --version` | https://nodejs.org |
| Claude Sonnet 4 model access enabled | Check in Bedrock console → Model access | https://console.aws.amazon.com/bedrock/home#/modelaccess |

### Enable Bedrock Model Access

1. Go to **AWS Console → Amazon Bedrock → Model access**
2. Click **Modify model access**
3. Enable **Anthropic → Claude Sonnet 4**
4. Click **Save changes** and wait for status to show "Access granted"

---

## Step 1: Clone and Set Up the Project

```bash
# Unzip the project
unzip bank-of-africa-agentcore.zip
cd bank-of-africa-agentcore
```

---

## Step 2: Set Up Python Environment

```bash
# Create a virtual environment
python3 -m venv .venv

# Activate it
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Install dependencies
pip install -r agentcore/agent/requirements.txt
```

You should see `strands-agents`, `bedrock-agentcore`, and `boto3` installed successfully.

---

## Step 3: Create DynamoDB Tables and Seed Data

This creates 3 tables (boa_users, boa_accounts, boa_transactions) and populates them with 5 Nigerian bank customers, 13 accounts, and ~1000 transactions.

```bash
# Set your AWS region (use the region where you have Bedrock access)
export AWS_DEFAULT_REGION=us-east-1

# Run the seed script
cd data
python3 seed_data.py
cd ..
```

**Expected output:**
```
Creating tables (if needed)...
Created boa_users table
Created boa_accounts table
Created boa_transactions table

Seeding Bank of Africa database...

  Added user: Adaeze Okonkwo (ID: 1)
  Added user: Chukwuemeka Nwosu (ID: 2)
  Added user: Fatima Abdullahi (ID: 3)
  Added user: Oluwaseun Adeyemi (ID: 4)
  Added user: Ngozi Eze (ID: 5)

  Added account: 1001 (Savings) for user 1 - NGN 2,750,000.00
  Added account: 1002 (Current) for user 1 - NGN 850,000.00
  ...

Done! Seeded 5 users, 13 accounts, ~1000 transactions.
```

**Verify the tables exist:**
```bash
aws dynamodb list-tables --query "TableNames[?starts_with(@, 'boa_')]"
```

---

## Step 4: Create the Bedrock Knowledge Base (Bank Handbook)

This gives the Knowledge Base Agent access to bank policies, fees, and rates.

### 4a. Create an S3 bucket and upload the handbook

```bash
# Create the bucket (use a unique name)
aws s3 mb s3://boa-handbook-$(aws sts get-caller-identity --query Account --output text) --region us-east-1

# Upload the handbook
aws s3 cp docs/bank_handbook.md s3://boa-handbook-$(aws sts get-caller-identity --query Account --output text)/
```

### 4b. Create the Knowledge Base in Bedrock Console

1. Go to **AWS Console → Amazon Bedrock → Knowledge Bases**
2. Click **Create Knowledge Base**
3. Name: `BankOfAfricaHandbook`
4. Data source: Choose **Amazon S3**
5. S3 URI: Select the bucket you just created
6. Embeddings model: **Titan Embeddings V2**
7. Vector store: **Quick create a new vector store** (uses OpenSearch Serverless)
8. Click **Create Knowledge Base**
9. Once created, click **Sync** to index the handbook
10. **Copy the Knowledge Base ID** (format: `XXXXXXXXXX`) — you need this in Step 5

---

## Step 5: Configure Environment Variables

```bash
# Set the Knowledge Base ID from Step 4
export KNOWLEDGE_BASE_ID=YOUR_KB_ID_HERE

# Set the AWS region
export AWS_DEFAULT_REGION=us-east-1
export AWS_REGION=us-east-1
```

---

## Step 6: Test the Agent Locally

Before deploying to AgentCore, test the agent on your local machine:

```bash
cd agent

# Run the agent locally
python3 agent.py
```

This starts the AgentCore local server on `http://localhost:8080`. Test it:

```bash
# In a new terminal window:
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Show me the profile for user 1"}'
```

**Expected response:** You should see Adaeze Okonkwo's profile data.

Try more queries:
```bash
# Check balances
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What are all the account balances for user 2?"}'

# Transfer funds
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Transfer NGN 100,000 from account 2001 to account 2002"}'

# Bank policy question
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What are the fees for international transfers?"}'
```

Press `Ctrl+C` to stop the local server when done.

---

## Step 7: Deploy to AgentCore Runtime

This packages your agent code, containerizes it, and deploys it to AgentCore Runtime with MicroVM isolation.

```bash
# Make sure you're in the agent directory
cd agent

# Step 7a: Configure AgentCore
agentcore configure -e agent.py --disable-memory

# Accept the defaults when prompted:
#   - Auto-create IAM role: Yes
#   - Auto-create ECR repository: Yes
#   - Region: us-east-1 (or your preferred region)
#   - Requirements file: requirements.txt (auto-detected)
```

```bash
# Step 7b: Deploy
agentcore deploy
```

**This will take 3-5 minutes.** It:
1. Packages your Python code
2. Builds an ARM64 container (via CodeBuild — no Docker needed locally)
3. Pushes to ECR
4. Creates the AgentCore Runtime agent
5. Returns the **Agent ARN**

**Expected output:**
```
✓ Agent deployed successfully!
Agent ARN: arn:aws:bedrock-agentcore:us-east-1:123456789012:agent-runtime/boa-XXXXXXX
```

**IMPORTANT: Copy the Agent ARN** — you need it for Step 8.

### Verify deployment:
```bash
agentcore status
```

### Test the deployed agent:
```bash
agentcore invoke --prompt "Show me the profile for user 2"
```

---

## Step 8: Set Up the API Gateway (for the React frontend)

The React frontend needs an API endpoint to talk to the AgentCore agent. We use a Lambda function behind API Gateway.

### 8a. Create the API Lambda

```bash
# Go back to project root
cd ..

# Create a Lambda deployment package
cd agent
zip api_lambda.zip api_handler.py
```

### 8b. Create the Lambda function

```bash
# Create IAM role for the Lambda (if not using CloudFormation)
aws iam create-role \
  --role-name boa-api-lambda-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# Attach policies
aws iam attach-role-policy \
  --role-name boa-api-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Add AgentCore invoke permission (inline policy)
aws iam put-role-policy \
  --role-name boa-api-lambda-role \
  --policy-name AgentCoreAccess \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": "bedrock-agentcore:InvokeAgentRuntime",
      "Resource": "*"
    }]
  }'

# Wait for role to propagate
sleep 10

# Create the Lambda function
aws lambda create-function \
  --function-name boa-api-handler \
  --runtime python3.12 \
  --handler api_handler.handler \
  --role arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/boa-api-lambda-role \
  --zip-file fileb://api_lambda.zip \
  --timeout 120 \
  --memory-size 512 \
  --environment "Variables={AGENT_RUNTIME_ARN=YOUR_AGENT_ARN_FROM_STEP_7}"
```

**IMPORTANT:** Replace `YOUR_AGENT_ARN_FROM_STEP_7` with the actual ARN from Step 7.

### 8c. Create API Gateway

```bash
# Create the REST API
API_ID=$(aws apigateway create-rest-api \
  --name "BankOfAfricaAPI" \
  --query 'id' --output text)

# Get the root resource ID
ROOT_ID=$(aws apigateway get-resources \
  --rest-api-id $API_ID \
  --query 'items[0].id' --output text)

# Create /chat resource
CHAT_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_ID \
  --path-part chat \
  --query 'id' --output text)

# Create POST method
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $CHAT_ID \
  --http-method POST \
  --authorization-type NONE

# Connect to Lambda
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=$(aws configure get region)

aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $CHAT_ID \
  --http-method POST \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:boa-api-handler/invocations"

# Grant API Gateway permission to invoke Lambda
aws lambda add-permission \
  --function-name boa-api-handler \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com

# Enable CORS — add OPTIONS method
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $CHAT_ID \
  --http-method OPTIONS \
  --authorization-type NONE

aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $CHAT_ID \
  --http-method OPTIONS \
  --type MOCK \
  --request-templates '{"application/json": "{\"statusCode\": 200}"}'

aws apigateway put-method-response \
  --rest-api-id $API_ID \
  --resource-id $CHAT_ID \
  --http-method OPTIONS \
  --status-code 200 \
  --response-parameters '{"method.response.header.Access-Control-Allow-Headers":false,"method.response.header.Access-Control-Allow-Methods":false,"method.response.header.Access-Control-Allow-Origin":false}'

aws apigateway put-integration-response \
  --rest-api-id $API_ID \
  --resource-id $CHAT_ID \
  --http-method OPTIONS \
  --status-code 200 \
  --response-parameters '{"method.response.header.Access-Control-Allow-Headers":"'\''Content-Type,Authorization'\''","method.response.header.Access-Control-Allow-Methods":"'\''POST,OPTIONS'\''","method.response.header.Access-Control-Allow-Origin":"'\''*'\''"}'

# Deploy the API
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name prod

echo ""
echo "✅ API Gateway deployed!"
echo "Your API URL: https://${API_ID}.execute-api.${REGION}.amazonaws.com/prod"
echo ""
echo "Update this URL in frontend/src/utils/api.js"
```

---

## Step 9: Configure and Run the React Frontend

### 9a. Update the API URL

Open `frontend/src/utils/api.js` and update line 7:

```javascript
// BEFORE:
const API_BASE_URL = process.env.REACT_APP_API_URL || "https://YOUR-API-ID.execute-api.af-south-1.amazonaws.com/prod";

// AFTER (use the URL from Step 8):
const API_BASE_URL = process.env.REACT_APP_API_URL || "https://abc123xyz.execute-api.us-east-1.amazonaws.com/prod";
```

### 9b. Install dependencies and run

```bash
cd frontend
npm install
npm start
```

The app opens at `http://localhost:3000`. You should see the Bank of Africa chat interface.

---

## Step 10: Test Everything End-to-End

Try these queries in the chat interface:

| Query | What Happens |
|-------|-------------|
| "Show me the profile for user 2" | Supervisor → Account Agent → get_user_profile |
| "What are all the balances for user 2?" | Supervisor → Account Agent → list_accounts → get_balance (×3) |
| "Show me recent transactions for account 2002" | Supervisor → Transaction Agent → get_recent_transactions |
| "Transfer NGN 100,000 from account 2001 to account 2002" | Supervisor → Transaction Agent → transfer_funds (validates balance first) |
| "What are the fees for international transfers?" | Supervisor → Knowledge Base Agent → search_bank_handbook |
| "Check if user 2 has enough in savings for a NGN 500,000 transfer to current, and if so, do it" | Supervisor → Account Agent (check) → Transaction Agent (transfer) → Account Agent (show updated balances) |

Click **"Show Agent Trace"** in the sidebar to see the Supervisor's reasoning and delegation in real time.

---

## Troubleshooting

### "Agent not configured" error in the frontend
→ Make sure you set `AGENT_RUNTIME_ARN` in the Lambda environment variables (Step 8b)

### "Access denied" when invoking the agent
→ Check that the Lambda IAM role has `bedrock-agentcore:InvokeAgentRuntime` permission

### DynamoDB "table not found" errors
→ Run `cd data && python3 seed_data.py` to create and populate tables
→ Verify tables exist: `aws dynamodb list-tables`

### Knowledge Base returns empty results
→ Make sure you synced the Knowledge Base in the Bedrock console (Step 4b, step 9)
→ Verify the `KNOWLEDGE_BASE_ID` environment variable is set correctly

### AgentCore deploy fails
→ Check `agentcore status` for error details
→ Verify you have the right IAM permissions: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-iam.html

### Slow responses (>30 seconds)
→ First invocation after deployment is slow (cold start). Subsequent invocations are faster.
→ The Supervisor may loop through multiple agents for complex queries — this is normal.

---

## Clean Up (After Workshop)

```bash
# Delete AgentCore agent
agentcore destroy

# Delete DynamoDB tables
aws dynamodb delete-table --table-name boa_users
aws dynamodb delete-table --table-name boa_accounts
aws dynamodb delete-table --table-name boa_transactions

# Delete Lambda function
aws lambda delete-function --function-name boa-api-handler

# Delete API Gateway
aws apigateway delete-rest-api --rest-api-id YOUR_API_ID

# Delete S3 bucket
aws s3 rb s3://boa-handbook-$(aws sts get-caller-identity --query Account --output text) --force

# Delete Knowledge Base (via Bedrock console)

# Delete IAM role
aws iam delete-role-policy --role-name boa-api-lambda-role --policy-name AgentCoreAccess
aws iam detach-role-policy --role-name boa-api-lambda-role --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
aws iam delete-role --role-name boa-api-lambda-role
```

---

## Architecture Summary

```
[React Chat UI] → [API Gateway] → [Lambda: api_handler.py]
                                         │
                                         ▼
                               [AgentCore Runtime]
                          (MicroVM — session isolation)
                                         │
                              [Supervisor Agent — Strands SDK]
                              (Swarm pattern orchestration)
                                         │
                    ┌────────────────────┼────────────────────┐
                    ▼                    ▼                    ▼
            [Account Agent]     [Transaction Agent]   [Knowledge Agent]
            @tool: 3 functions  @tool: 3 functions    @tool: 1 function
                    │                    │                    │
                    ▼                    ▼                    ▼
              [DynamoDB]           [DynamoDB]          [Bedrock KB]
            boa_users            boa_transactions    (S3 → OpenSearch)
            boa_accounts
```
