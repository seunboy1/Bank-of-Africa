"""
Bank of Africa — List Accounts
Returns all accounts belonging to a user.
"""
import json
import boto3
from decimal import Decimal

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = "boa_accounts"


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)


def handler(event, context):
    params = extract_params(event)
    user_id = params.get("user_id", "")

    if not user_id:
        return agent_response(event, "Error: user_id is required.")

    table = dynamodb.Table(TABLE_NAME)

    try:
        # Query using GSI on user_id
        response = table.query(
            IndexName="user_id-index",
            KeyConditionExpression="user_id = :uid",
            ExpressionAttributeValues={":uid": user_id},
        )
        accounts = response.get("Items", [])

        if not accounts:
            return agent_response(event, f"No accounts found for user ID: {user_id}")

        lines = [f"Accounts for User {user_id}:\n"]
        for i, acct in enumerate(accounts, 1):
            lines.append(
                f"Account {i}:\n"
                f"  - Account ID: {acct.get('account_id')}\n"
                f"  - Type: {acct.get('account_type', 'N/A')}\n"
                f"  - Balance: NGN {float(acct.get('balance', 0)):,.2f}\n"
                f"  - Currency: {acct.get('currency', 'NGN')}\n"
                f"  - Status: {acct.get('status', 'active')}\n"
            )

        return agent_response(event, "\n".join(lines))

    except Exception as e:
        return agent_response(event, f"Error listing accounts: {str(e)}")


def extract_params(event):
    params = {}
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
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event.get("actionGroup", ""),
            "apiPath": event.get("apiPath", ""),
            "httpMethod": event.get("httpMethod", "GET"),
            "httpStatusCode": 200,
            "responseBody": {"application/json": {"body": body}},
        },
    }
