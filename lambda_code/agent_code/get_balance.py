"""
Bank of Africa — Get Account Balance
Returns the balance for a specific account.
"""
import json
import boto3
from decimal import Decimal

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = "boa_accounts"


def handler(event, context):
    params = extract_params(event)
    account_id = params.get("account_id", "")

    if not account_id:
        return agent_response(event, "Error: account_id is required.")

    table = dynamodb.Table(TABLE_NAME)

    try:
        response = table.get_item(Key={"account_id": account_id})
        acct = response.get("Item")

        if not acct:
            return agent_response(event, f"No account found with ID: {account_id}")

        result = (
            f"Account Balance:\n"
            f"- Account ID: {acct.get('account_id')}\n"
            f"- Type: {acct.get('account_type', 'N/A')}\n"
            f"- Balance: NGN {float(acct.get('balance', 0)):,.2f}\n"
            f"- Currency: {acct.get('currency', 'NGN')}\n"
            f"- Status: {acct.get('status', 'active')}"
        )

        return agent_response(event, result)

    except Exception as e:
        return agent_response(event, f"Error getting balance: {str(e)}")


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
