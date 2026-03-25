#!/bin/bash
# ============================================================
# 🧹 Bank of Africa — CLEANUP
# Run this after the workshop to remove all AWS resources.
# ============================================================

STACK_NAME="bank-of-africa"
REGION="${AWS_DEFAULT_REGION:-us-east-1}"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "🧹 Cleaning up Bank of Africa resources..."

# Empty S3 buckets (required before stack deletion)
echo "  Emptying S3 buckets..."
aws s3 rm s3://boa-handbook-${ACCOUNT_ID}/ --recursive 2>/dev/null || true
aws s3 rm s3://boa-frontend-${ACCOUNT_ID}/ --recursive 2>/dev/null || true
aws s3 rm s3://boa-deploy-${ACCOUNT_ID}-${REGION}/ --recursive 2>/dev/null || true

# Delete the CloudFormation stack
echo "  Deleting CloudFormation stack: ${STACK_NAME}..."
aws cloudformation delete-stack --stack-name ${STACK_NAME} --region ${REGION}
aws cloudformation wait stack-delete-complete --stack-name ${STACK_NAME} --region ${REGION} 2>/dev/null

# Delete the deploy bucket
aws s3 rb s3://boa-deploy-${ACCOUNT_ID}-${REGION} --force 2>/dev/null || true

echo "✅ All resources deleted."
