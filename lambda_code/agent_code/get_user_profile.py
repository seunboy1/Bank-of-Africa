"""
Bank of Africa — Get User Profile
Lambda function for the Account Management Agent.
Returns customer profile data from DynamoDB.
"""
import json
import boto3

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = "boa_users"


def handler(event, context):
    """
    Bedrock Agent action group handler.
    Expects: user_id parameter from the agent.
    Returns: user profile as structured text.
    """
    # Extract parameters from Bedrock Agent event
    params = extract_params(event)
    user_id = params.get("user_id", "")

    if not user_id:
        return agent_response(event, "Error: user_id is required.")

    table = dynamodb.Table(TABLE_NAME)

    try:
        response = table.get_item(Key={"user_id": user_id})
        user = response.get("Item")

        if not user:
            return agent_response(event, f"No user found with ID: {user_id}")

        result = (
            f"User Profile for {user.get('full_name', 'N/A')}:\n"
            f"- User ID: {user.get('user_id')}\n"
            f"- Email: {user.get('email', 'N/A')}\n"
            f"- Phone: {user.get('phone', 'N/A')}\n"
            f"- Address: {user.get('address', 'N/A')}\n"
            f"- BVN: {user.get('bvn', 'N/A')}\n"
            f"- Date Joined: {user.get('date_joined', 'N/A')}\n"
            f"- KYC Tier: {user.get('kyc_tier', 'N/A')}"
        )

        return agent_response(event, result)

    except Exception as e:
        return agent_response(event, f"Error retrieving user profile: {str(e)}")


def extract_params(event):
    """Extract parameters from Bedrock Agent event format."""
    params = {}
    # Handle both direct invocation and Bedrock Agent formats
    if "parameters" in event:
        for param in event["parameters"]:
            params[param["name"]] = param["value"]
    elif "requestBody" in event:
        content = event["requestBody"].get("content", {})
        props = content.get("application/json", {}).get("properties", [])
        for prop in props:
            params[prop["name"]] = prop["value"]
    else:
        params = event
    return params


def agent_response(event, body):
    """Format response for Bedrock Agent."""
    action_group = event.get("actionGroup", "")
    api_path = event.get("apiPath", "")

    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": action_group,
            "apiPath": api_path,
            "httpMethod": event.get("httpMethod", "GET"),
            "httpStatusCode": 200,
            "responseBody": {
                "application/json": {
                    "body": body
                }
            },
        },
    }
