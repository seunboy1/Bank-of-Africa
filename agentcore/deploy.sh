#!/bin/bash
# ============================================================
# Bank of Africa — AgentCore Deployment Script
# Deploys the Strands Agents + AgentCore Runtime banking system
# ============================================================

set -e

echo "🏦 Bank of Africa — AgentCore Deployment"
echo "========================================="

# Step 1: Check prerequisites
echo ""
echo "Step 1: Checking prerequisites..."
python3 --version || { echo "❌ Python 3.10+ required"; exit 1; }
aws sts get-caller-identity > /dev/null 2>&1 || { echo "❌ AWS CLI not configured"; exit 1; }
echo "✅ Prerequisites met"

# Step 2: Set up Python virtual environment
echo ""
echo "Step 2: Setting up Python environment..."
cd agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
echo "✅ Dependencies installed"

# Step 3: Seed DynamoDB data
echo ""
echo "Step 3: Seeding DynamoDB with Nigerian banking data..."
cd ../data
python3 seed_data.py
cd ../agent
echo "✅ Database seeded"

# Step 4: Configure AgentCore
echo ""
echo "Step 4: Configuring AgentCore Runtime..."
echo "  → This will create IAM roles and ECR repository"
agentcore configure -e agent.py --disable-memory
echo "✅ AgentCore configured"

# Step 5: Deploy to AgentCore Runtime
echo ""
echo "Step 5: Deploying agent to AgentCore Runtime..."
echo "  → This packages your code, builds the container, and deploys"
agentcore deploy
echo "✅ Agent deployed!"

# Step 6: Get the Agent ARN
echo ""
echo "Step 6: Agent details:"
echo "  → Check .bedrock_agentcore.yaml for your Agent ARN"
echo "  → Use this ARN in the React frontend API configuration"
cat .bedrock_agentcore.yaml 2>/dev/null || echo "  (config file not found — check agentcore status)"

# Step 7: Test the agent
echo ""
echo "Step 7: Testing the agent..."
agentcore invoke --prompt "Show me the profile for user 1"

echo ""
echo "========================================="
echo "🎉 Bank of Africa is live on AgentCore!"
echo ""
echo "Next steps:"
echo "  1. Copy the Agent ARN from above"
echo "  2. Set it as AGENT_RUNTIME_ARN in the API handler Lambda"
echo "  3. Deploy the API Gateway + Lambda (see template.yaml)"
echo "  4. Update frontend/src/utils/api.js with the API Gateway URL"
echo "  5. Run: cd frontend && npm install && npm start"
echo "========================================="
