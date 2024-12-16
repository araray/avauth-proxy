from flask import Blueprint, render_template, session, redirect, url_for
from avauth_proxy.utils.oauth_utils import load_oauth_providers, oauth

auth_bp = Blueprint("auth", __name__)

oauth_providers = load_oauth_providers(oauth)

@auth_bp.route("/login")
def login():
    providers = oauth_providers.values()
    return render_template("auth/login.html", providers=providers)

@auth_bp.route("/login/<provider_name>")
def oauth_login(provider_name):
    if provider_name not in oauth_providers:
        return "Unsupported provider", 400
    redirect_uri = url_for("auth.authorize", provider_name=provider_name, _external=True)
    return oauth.create_client(provider_name).authorize_redirect(redirect_uri)

@auth_bp.route("/authorize/<provider_name>")
def authorize(provider_name):
    if provider_name not in oauth_providers:
        return "Unsupported provider", 400
    try:
        client = oauth.create_client(provider_name)
        token = client.authorize_access_token()
        user_info = client.userinfo()
        session["user"] = user_info
        return redirect(url_for("proxy.dashboard"))
    except Exception as e:
        return f"Authentication failed: {e}"

@auth_bp.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("auth.login"))
