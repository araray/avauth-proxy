from flask import Flask, request, jsonify
from authlib.integrations.flask_oauth2 import AuthorizationServer
from authlib.oauth2.rfc6749 import grants
from authlib.common.security import generate_token
from werkzeug.security import gen_salt
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'replace-with-a-secure-random-string'

# In-memory storage for simplicity
users = {
    'araray': {'password': 'teste'}
}

clients = {}

tokens = {}

def current_time():
    return datetime.utcnow()

def query_client(client_id):
    return clients.get(client_id)

def save_token(token, request):
    tokens[token['access_token']] = token

# Configure Authorization Server
authorization = AuthorizationServer(
    app,
    query_client=query_client,
    save_token=save_token,
)

# Define Grant Types
class PasswordGrant(grants.ResourceOwnerPasswordCredentialsGrant):
    def authenticate_user(self, username, password):
        user = users.get(username)
        if user and user['password'] == password:
            return username  # Returning username as user ID
        return None

    def save_token(self, token_data, request):
        save_token(token_data, request)

authorization.register_grant(PasswordGrant)

@app.route('/oauth/token', methods=['POST'])
def issue_token():
    return authorization.create_token_response()

# Endpoint to register a client (for testing purposes)
@app.route('/client/register', methods=['POST'])
def register_client():
    client_id = gen_salt(24)
    client_secret = gen_salt(48)
    redirect_uris = request.form.get('redirect_uris', '').split()

    clients[client_id] = {
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uris': redirect_uris,
        'token_endpoint_auth_method': 'client_secret_basic',
        'grant_types': ['password'],
        'response_types': [],
        'scope': 'read write'
    }

    return jsonify({
        'client_id': client_id,
        'client_secret': client_secret
    })

if __name__ == '__main__':
    app.run(port=6000, debug=True)

