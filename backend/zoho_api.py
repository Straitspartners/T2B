from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import os
import requests
import jwt
import datetime
import bcrypt
import sqlite3

load_dotenv()

app = Flask(__name__)
CORS(app)

SECRET_KEY = "your_secret_key_here_minimum_32_characters_long"

CLIENT_ID = os.getenv("ZOHO_CLIENT_ID")
CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("ZOHO_REFRESH_TOKEN")
ORG_ID = os.getenv("ZOHO_ORG_ID")


# ✅ DATABASE SETUP
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database on startup
init_db()


# ✅ REGISTER
@app.route("/T2B/api/register", methods=["POST"])
def register():
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({"error": "All fields are required"}), 400

    try:
        conn = get_db()
        cursor = conn.cursor()

        # Check if user exists
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            conn.close()
            return jsonify({"error": "User already exists"}), 400

        # Hash password and save
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (name, email, hashed.decode("utf-8"))
        )
        conn.commit()
        conn.close()

        token = jwt.encode({
            "email": email,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }, SECRET_KEY, algorithm="HS256")

        return jsonify({"token": token, "name": name, "email": email}), 200

    except Exception as e:
        print("Register error:", e)
        return jsonify({"error": "Registration failed"}), 500


# ✅ SIGNIN
@app.route("/T2B/api/signin", methods=["POST"])
def signin():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "All fields are required"}), 400

    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if not user or not bcrypt.checkpw(
            password.encode("utf-8"),
            user["password"].encode("utf-8")
        ):
            return jsonify({"error": "Invalid credentials"}), 401

        token = jwt.encode({
            "email": email,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }, SECRET_KEY, algorithm="HS256")

        return jsonify({"token": token, "email": email, "name": user["name"]}), 200

    except Exception as e:
        print("Signin error:", e)
        return jsonify({"error": "Signin failed"}), 500


# ✅ CONNECT ZOHO
@app.route("/T2B/api/connect-zoho", methods=["POST"])
def connect_zoho():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Authentication token not found. Please login again."}), 401

    token = auth_header.split(" ")[1]
    try:
        jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired. Please login again."}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token. Please login again."}), 401

    data = request.get_json()
    client_id = data.get("client_id")
    client_secret = data.get("client_secret")
    access_token = data.get("access_token")
    refresh_token = data.get("refresh_token")
    organization_id = data.get("organization_id")

    if not all([client_id, client_secret, access_token, refresh_token, organization_id]):
        return jsonify({"error": "All Zoho credentials are required"}), 400

    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}"
    }

    test_response = requests.get(
        "https://www.zohoapis.com/books/v3/organizations",
        headers=headers
    )

    print("Zoho status:", test_response.status_code)
    print("Zoho response:", test_response.json())

    if test_response.status_code != 200:
        return jsonify({
            "error": "Invalid Zoho credentials. Please check and try again.",
            "zoho_response": test_response.json()
        }), 400

    return jsonify({"message": "Zoho Books connected successfully!"}), 200


# ✅ TOKEN HELPER
def get_access_token():
    url = "https://accounts.zoho.com/oauth/v2/token"
    params = {
        "refresh_token": REFRESH_TOKEN,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token"
    }
    response = requests.post(url, params=params)
    data = response.json()
    return data.get("access_token")


# ✅ ZOHO ROUTES
@app.route("/api/zoho/organizations")
def organizations():
    access_token = get_access_token()
    headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
    response = requests.get(
        "https://www.zohoapis.in/books/v3/organizations",
        headers=headers
    )
    return jsonify(response.json())


@app.route("/api/zoho/customers")
def customers():
    access_token = get_access_token()
    headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
    response = requests.get(
        f"https://www.zohoapis.in/books/v3/contacts?organization_id={ORG_ID}",
        headers=headers
    )
    return jsonify(response.json())


@app.route("/api/zoho/invoices")
def invoices():
    access_token = get_access_token()
    headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
    response = requests.get(
        f"https://www.zohoapis.in/books/v3/invoices?organization_id={ORG_ID}",
        headers=headers
    )
    return jsonify(response.json())


if __name__ == "__main__":
    app.run(port=5000, debug=True)