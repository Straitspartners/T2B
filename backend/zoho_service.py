import logging
import os
import time

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify


# Load environment variables from backend/.env before reading credentials.
load_dotenv()


# Configure basic logging so token/API failures are visible in the terminal.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


app = Flask(__name__)


ZOHO_TOKEN_URL = "https://accounts.zoho.com/oauth/v2/token"
ZOHO_BOOKS_API_BASE_URL = "https://www.zohoapis.in/books/v3"


# Keep the current access token in memory. Zoho access tokens are short-lived,
# so this service refreshes them automatically when needed.
_cached_access_token = None
_cached_access_token_expires_at = 0


def get_required_env(name):
    """Read a required environment variable or raise a clear error."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def get_access_token():
    """Generate or reuse a valid Zoho OAuth access token."""
    global _cached_access_token, _cached_access_token_expires_at

    if _cached_access_token and time.time() < _cached_access_token_expires_at:
        return _cached_access_token

    payload = {
        "refresh_token": get_required_env("ZOHO_REFRESH_TOKEN"),
        "client_id": get_required_env("ZOHO_CLIENT_ID"),
        "client_secret": get_required_env("ZOHO_CLIENT_SECRET"),
        "grant_type": "refresh_token",
    }

    try:
        logger.info("Requesting fresh Zoho access token")
        response = requests.post(ZOHO_TOKEN_URL, data=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        access_token = data.get("access_token")
        if not access_token:
            logger.error("Zoho token response missing access_token: %s", data)
            raise RuntimeError("Zoho token response did not include access_token")

        expires_in = int(data.get("expires_in", 3600))
        _cached_access_token = access_token
        _cached_access_token_expires_at = time.time() + max(expires_in - 60, 60)

        logger.info("Zoho access token generated successfully")
        return _cached_access_token
    except requests.RequestException as exc:
        error_body = exc.response.text if exc.response is not None else str(exc)
        logger.exception("Failed to generate Zoho access token: %s", error_body)
        raise


def call_zoho_books(path, params=None):
    """Call Zoho Books with a fresh OAuth token and return parsed JSON."""
    params = params or {}
    access_token = get_access_token()
    url = f"{ZOHO_BOOKS_API_BASE_URL}{path}"

    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
    }

    try:
        logger.info("Calling Zoho Books API: %s params=%s", path, params)
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        error_body = exc.response.text if exc.response is not None else str(exc)
        logger.exception("Zoho Books API request failed: %s", error_body)
        raise


def error_response(message, exc):
    """Return consistent JSON errors from Flask routes."""
    status_code = exc.response.status_code if getattr(exc, "response", None) is not None else 500
    details = exc.response.text if getattr(exc, "response", None) is not None else str(exc)

    return jsonify({
        "message": message,
        "details": details,
    }), status_code


@app.get("/api/health")
def health_check():
    """Simple route to confirm the Flask backend is running."""
    return jsonify({
        "status": "ok",
        "service": "tally-to-books-zoho-api",
    })


@app.get("/api/zoho/organizations")
def get_organizations():
    """Return Zoho Books organizations available to this OAuth account."""
    try:
        data = call_zoho_books("/organizations")
        return jsonify(data)
    except Exception as exc:
        return error_response("Failed to fetch Zoho organizations", exc)


@app.get("/api/zoho/customers")
def get_customers():
    """Return Zoho Books customers. Zoho stores customers as contacts."""
    try:
        data = call_zoho_books("/contacts", {
            "organization_id": get_required_env("ZOHO_ORG_ID"),
        })
        return jsonify(data)
    except Exception as exc:
        return error_response("Failed to fetch Zoho customers", exc)


@app.get("/api/zoho/invoices")
def get_invoices():
    """Return Zoho Books invoices for the configured organization."""
    try:
        data = call_zoho_books("/invoices", {
            "organization_id": get_required_env("ZOHO_ORG_ID"),
        })
        return jsonify(data)
    except Exception as exc:
        return error_response("Failed to fetch Zoho invoices", exc)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
