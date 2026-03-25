#!/usr/bin/env python3
"""
Bank of Africa — AWS CDK Deployment
Deploys the complete agentic banking system using CDK (Python).

Usage:
    pip install aws-cdk-lib constructs
    cdk bootstrap
    cdk deploy
"""

import aws_cdk as cdk
from stacks.boa_stack import BankOfAfricaStack

app = cdk.App()

BankOfAfricaStack(
    app,
    "BankOfAfricaStack",
    description="Bank of Africa — Complete Agentic AI Banking System",
    env=cdk.Environment(
        region="us-east-1",  # Change to your preferred region
    ),
)

app.synth()
