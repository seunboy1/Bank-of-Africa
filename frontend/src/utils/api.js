/**
 * Bank of Africa — API Client
 * Handles communication between React frontend and the Bedrock Agent via API Gateway.
 */

// API URL is injected at deploy time via env-config.js, or use environment variable for local dev
const API_BASE_URL =
  window.ENV_CONFIG?.API_BASE_URL !== "PLACEHOLDER_API_URL"
    ? window.ENV_CONFIG?.API_BASE_URL
    : process.env.REACT_APP_API_URL || "http://localhost:3001";

/**
 * Send a message to the Bank of Africa AI Assistant.
 * @param {string} message - The user's message
 * @param {string} sessionId - Session ID for conversation continuity
 * @returns {Promise<{response: string, session_id: string, traces: Array}>}
 */
export async function sendMessage(message, sessionId) {
  const res = await fetch(`${API_BASE_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId }),
  });

  if (!res.ok) {
    const errBody = await res.json().catch(() => ({}));
    throw new Error(errBody.error || `Request failed with status ${res.status}`);
  }

  return res.json();
}

/**
 * Generate a unique session ID.
 */
export function createSessionId() {
  return "boa-" + crypto.randomUUID();
}

/**
 * Suggested prompts for the workshop demo.
 */
export const SUGGESTED_PROMPTS = [
  {
    icon: "👤",
    label: "View profile",
    text: "Show me the profile for user 2",
  },
  {
    icon: "💰",
    label: "Check balances",
    text: "What are all the account balances for user 2?",
  },
  {
    icon: "📜",
    label: "Transaction history",
    text: "Show me the recent transactions for account 2002",
  },
  {
    icon: "💸",
    label: "Transfer funds",
    text: "Transfer NGN 100,000 from account 2001 to account 2002",
  },
  {
    icon: "📖",
    label: "Bank policies",
    text: "What are the fees for international transfers?",
  },
  {
    icon: "🏦",
    label: "Account types",
    text: "What types of accounts does Bank of Africa offer and what are the interest rates?",
  },
  {
    icon: "⚡",
    label: "Multi-step request",
    text: "Check if user 2's savings account has enough for a NGN 500,000 transfer to their current account. If yes, do the transfer and show updated balances.",
  },
  {
    icon: "🔒",
    label: "KYC tiers",
    text: "What are the KYC tier requirements and transaction limits?",
  },
];
