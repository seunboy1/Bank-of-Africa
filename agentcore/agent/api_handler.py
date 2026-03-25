"""
Bank of Africa — API Handler
Lambda function behind API Gateway that invokes the AgentCore Runtime agent.
This bridges the React frontend to the deployed AgentCore agent.
"""

import json
import os
import uuid
import boto3

agentcore_client = boto3.client(
    "bedrock-agentcore",
    region_name=os.environ.get("AWS_REGION", "us-east-1"),
)

AGENT_RUNTIME_ARN = os.environ.get("AGENT_RUNTIME_ARN", "")

HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "POST,OPTIONS",
    "Content-Type": "application/json",
}


def handler(event, context):
    """Handle API Gateway requests and invoke AgentCore Runtime."""

    # CORS preflight
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": HEADERS, "body": ""}

    try:
        body = json.loads(event.get("body", "{}"))
        user_message = body.get("message", "")
        session_id = body.get("session_id", str(uuid.uuid4()))

        if not user_message:
            return {
                "statusCode": 400,
                "headers": HEADERS,
                "body": json.dumps({"error": "Message is required"}),
            }

        if not AGENT_RUNTIME_ARN:
            return {
                "statusCode": 500,
                "headers": HEADERS,
                "body": json.dumps({"error": "Agent not configured. Set AGENT_RUNTIME_ARN."}),
            }

        # Invoke AgentCore Runtime
        payload = json.dumps({
            "prompt": user_message,
            "session_id": session_id,
        })

        response = agentcore_client.invoke_agent_runtime(
            agentRuntimeArn=AGENT_RUNTIME_ARN,
            qualifier="DEFAULT",
            payload=payload,
        )

        # Parse response
        response_body = response["response"].read()
        response_data = json.loads(response_body)

        return {
            "statusCode": 200,
            "headers": HEADERS,
            "body": json.dumps({
                "response": response_data.get("response", ""),
                "session_id": session_id,
                "agent": response_data.get("agent", "BankOfAfricaSupervisor"),
            }),
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": HEADERS,
            "body": json.dumps({"error": str(e)}),
        }
