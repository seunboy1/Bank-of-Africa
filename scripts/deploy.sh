#!/bin/bash
# ============================================================
# 🏦 Bank of Africa — ONE-CLICK DEPLOY
# ============================================================
# Paste this ENTIRE script into AWS CloudShell.
# It deploys the full Bank of Africa Agentic AI Banking System.
# Expected time: ~10-12 minutes.
#
# What gets deployed:
#   - 3 DynamoDB tables (auto-seeded with Nigerian banking data)
#   - S3 bucket with bank handbook
#   - Bedrock Knowledge Base (auto-synced)
#   - 7 Lambda functions
#   - API Gateway with CORS
#   - React frontend on S3 + CloudFront
#   - AgentCore agent (Strands SDK + Swarm pattern)
#
# At the end, you get a URL. Click it. Start banking.
# ============================================================

set -e

STACK_NAME="bank-of-africa"
REGION="${AWS_DEFAULT_REGION:-us-east-1}"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo ""
echo "🏦 ==========================================="
echo "   Bank of Africa — Deploying..."
echo "   Account: ${ACCOUNT_ID}"
echo "   Region:  ${REGION}"
echo "==========================================="
echo ""

# Step 1: Clone the repository
echo "📦 Step 1/5: Cloning repository..."
cd /tmp
if [ -d "BankAfrica" ]; then rm -rf BankAfrica; fi

git clone https://github.com/seunboy1/BankAfrica.git
cd BankAfrica
echo "✅ Repository cloned"

# Step 2: Package Lambda functions
echo ""
echo "📦 Step 2/5: Packaging Lambda functions..."
cd cfn

# Create deployment bucket
DEPLOY_BUCKET="boa-deploy-${ACCOUNT_ID}-${REGION}"
aws s3 mb s3://${DEPLOY_BUCKET} --region ${REGION} 2>/dev/null || true

# Package the SAM template
aws cloudformation package \
    --template-file template.yaml \
    --s3-bucket ${DEPLOY_BUCKET} \
    --output-template-file packaged.yaml \
    --region ${REGION} \
    > /dev/null 2>&1

echo "✅ Lambda functions packaged"

# Step 3: Deploy the stack
echo ""
echo "🚀 Step 3/5: Deploying CloudFormation stack (this takes ~8-10 min)..."
echo "   Go grab a coffee ☕ or check your phone 📱"
echo ""

aws cloudformation deploy \
    --template-file packaged.yaml \
    --stack-name ${STACK_NAME} \
    --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
    --region ${REGION} \
    --parameter-overrides \
        ProjectName=${STACK_NAME} \
    --no-fail-on-empty-changeset

echo "✅ Stack deployed"

# Step 4: Get outputs
echo ""
echo "📋 Step 4/5: Retrieving endpoints..."

API_URL=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" \
    --output text --region ${REGION})

FRONTEND_URL=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --query "Stacks[0].Outputs[?OutputKey=='FrontendURL'].OutputValue" \
    --output text --region ${REGION})

AGENT_ARN=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --query "Stacks[0].Outputs[?OutputKey=='AgentCoreARN'].OutputValue" \
    --output text --region ${REGION})

# Step 5: Deploy frontend with the correct API URL baked in
echo ""
echo "🌐 Step 5/5: Deploying React frontend..."

FRONTEND_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --query "Stacks[0].Outputs[?OutputKey=='FrontendBucket'].OutputValue" \
    --output text --region ${REGION})

# Check for pre-built frontend
if [ -d "frontend/build" ]; then
    cd frontend/build
elif [ -d "frontend-dist" ]; then
    cd frontend-dist
else
    echo "❌ No pre-built frontend found."
    echo "   Expected: frontend/build or frontend-dist folder"
    echo "   Run 'cd frontend && npm run build' locally and push to GitHub."
    exit 1
fi

# Inject API URL into the config
if [ -f "env-config.js" ]; then
    sed -i "s|PLACEHOLDER_API_URL|${API_URL}|g" env-config.js
fi

# Upload frontend to S3
aws s3 sync . s3://${FRONTEND_BUCKET}/ --delete --region ${REGION} > /dev/null 2>&1

echo "✅ Frontend deployed"

# Done!
echo ""
echo "🏦 ==========================================="
echo "   BANK OF AFRICA IS LIVE!"
echo "==========================================="
echo ""
echo "🌐 Chat App:    ${FRONTEND_URL:-Check CloudFormation outputs}"
echo "🔌 API:         ${API_URL}"
echo "🤖 Agent ARN:   ${AGENT_ARN:-Deploying...}"
echo ""
echo "👉 Open the Chat App URL above and start banking!"
echo ""
echo "Try these queries:"
echo "  • Show me the profile for user 2"
echo "  • What are all the balances for user 2?"
echo "  • Transfer NGN 100,000 from account 2001 to account 2002"
echo "  • What are the fees for international transfers?"
echo ""
echo "==========================================="
