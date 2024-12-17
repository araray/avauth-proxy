from flask import Flask, request, jsonify
from authlib.integrations.flask_oauth2 import AuthorizationServer
from authlib.oauth2.rfc6749 import grants
from werkzeug.security import gen_salt
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "mock-oauth2-server-secret-key"

users = {
    "testuser": {"password": "password123", "email": "testuser@example.com", "name": "Test User"}
}

clients = {}
tokens = {}

def current_time():
    return datetime.utcnow()

def generate_user_info(user_id):
    user = users.get(user_id)
    if user:
        return {
            "sub": user_id,
            "name": user.get("name"),
            "email": user.get("email"),
        }
    return None

def query_client(client_id):
    return clients.get(client_id)

def save_token(token, request):
    tokens[token["access_token"]] = {
        "token": token,
        "user_id": request.user,
        "expires_at": current_time() + timedelta(seconds=token["expires_in"]),
    }

class PasswordGrant(grants.ResourceOwnerPasswordCredentialsGrant):
    def authenticate_user(self, username, password):
        user = users.get(username)
        if user and user["password"] == password:
            return username
        return None

    def save_token(self, token_data, request):
        save_token(token_data, request)

authorization = AuthorizationServer(app, query_client=query_client, save_token=save_token)
authorization.register_grant(PasswordGrant)

@app.route("/health")
def health():
    return "OK", 200

@app.route("/oauth/token", methods=["POST"])
def issue_token():
    return authorization.create_token_response()

@app.route("/oauth/userinfo", methods=["GET"])
def user_info():
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "").strip()
    token_data = tokens.get(token)

    if not token_data or token_data["expires_at"] < current_time():
        return jsonify({"error": "invalid_token"}), 401

    user_info = generate_user_info(token_data["user_id"])
    if not user_info:
        return jsonify({"error": "user_not_found"}), 404

    return jsonify(user_info)

@app.route("/client/register", methods=["POST"])
def register_client():
    client_id = gen_salt(24)
    client_secret = gen_salt(48)
    redirect_uris = request.form.get("redirect_uris", "").split()

    clients = {
        "mock_client_id": {
            "client_id": "mock_client_id",
            "client_secret": "mock_client_secret",
            "redirect_uris": [],
            "token_endpoint_auth_method": "client_secret_basic",
            "grant_types": ["password"],
            "response_types": [],
            "scope": "read write"
        }
    }

    return jsonify({"client_id": client_id, "client_secret": client_secret})


@app.route("/oauth/authorize", methods=["GET", "POST"])
def mock_authorize():
    return jsonify({"message": "Authorization endpoint not implemented. Use the password grant instead."}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6000, debug=True)
