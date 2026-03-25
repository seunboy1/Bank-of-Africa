"""
Bank of Africa — Account Management Tools
Strands Agents custom tools for the Account Management Agent.
Each function uses the @tool decorator to register with the agent.
"""

import boto3
from decimal import Decimal
from strands import tool

dynamodb = boto3.resource("dynamodb")
USERS_TABLE = "boa_users"
ACCOUNTS_TABLE = "boa_accounts"


@tool
def get_user_profile(user_id: str) -> str:
    """
    Get a customer's profile information from the bank database.

    Args:
        user_id: The unique identifier of the bank customer (e.g., "1", "2", "3")

    Returns:
        A formatted string with the customer's profile including name, email,
        phone, address, BVN, KYC tier, and account summary.
    """
    table = dynamodb.Table(USERS_TABLE)

    try:
        response = table.get_item(Key={"user_id": user_id})
        user = response.get("Item")

        if not user:
            return f"No user found with ID: {user_id}"

        return (
            f"User Profile:\n"
            f"- Name: {user.get('full_name', 'N/A')}\n"
            f"- User ID: {user.get('user_id')}\n"
            f"- Email: {user.get('email', 'N/A')}\n"
            f"- Phone: {user.get('phone', 'N/A')}\n"
            f"- Address: {user.get('address', 'N/A')}\n"
            f"- BVN: {user.get('bvn', 'N/A')}\n"
            f"- KYC Tier: {user.get('kyc_tier', 'N/A')}\n"
            f"- Date Joined: {user.get('date_joined', 'N/A')}"
        )
    except Exception as e:
        return f"Error retrieving profile: {str(e)}"


@tool
def list_accounts(user_id: str) -> str:
    """
    List all bank accounts belonging to a customer.

    Args:
        user_id: The unique identifier of the bank customer (e.g., "1", "2", "3")

    Returns:
        A formatted list of all accounts with account IDs, types, balances, and currencies.
    """
    table = dynamodb.Table(ACCOUNTS_TABLE)

    try:
        response = table.query(
            IndexName="user_id-index",
            KeyConditionExpression="user_id = :uid",
            ExpressionAttributeValues={":uid": user_id},
        )
        accounts = response.get("Items", [])

        if not accounts:
            return f"No accounts found for user ID: {user_id}"

        lines = [f"Accounts for User {user_id}:\n"]
        for i, acct in enumerate(accounts, 1):
            balance = float(acct.get("balance", 0))
            lines.append(
                f"Account {i}:\n"
                f"  - Account ID: {acct.get('account_id')}\n"
                f"  - Type: {acct.get('account_type', 'N/A')}\n"
                f"  - Balance: NGN {balance:,.2f}\n"
                f"  - Currency: {acct.get('currency', 'NGN')}\n"
                f"  - Status: {acct.get('status', 'active')}\n"
            )

        return "\n".join(lines)
    except Exception as e:
        return f"Error listing accounts: {str(e)}"


@tool
def get_balance(account_id: str) -> str:
    """
    Get the current balance for a specific bank account.

    Args:
        account_id: The unique account identifier (e.g., "1001", "2002")

    Returns:
        The account balance with type and currency information.
    """
    table = dynamodb.Table(ACCOUNTS_TABLE)

    try:
        response = table.get_item(Key={"account_id": account_id})
        acct = response.get("Item")

        if not acct:
            return f"No account found with ID: {account_id}"

        balance = float(acct.get("balance", 0))
        return (
            f"Account {account_id}:\n"
            f"- Type: {acct.get('account_type', 'N/A')}\n"
            f"- Balance: NGN {balance:,.2f}\n"
            f"- Currency: {acct.get('currency', 'NGN')}\n"
            f"- Status: {acct.get('status', 'active')}"
        )
    except Exception as e:
        return f"Error getting balance: {str(e)}"
