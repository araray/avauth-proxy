from flask import Blueprint, render_template, session, redirect, url_for
from avauth_proxy.utils.oauth_utils import load_oauth_providers
from avauth_proxy.config import Config
from avauth_proxy import oauth

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login")
def login():
    """
    Display a login page if internal OAuth is enabled.
    If oauth2-proxy is used, this endpoint might be unnecessary.
    """
    if Config.USE_OAUTH2_PROXY:
        # If using oauth2-proxy, user shouldn't reach here.
        return redirect("/oauth2/sign_in")

    providers = load_oauth_providers(oauth)
    providers_list = providers.values()
    return render_template("auth/login.html", providers=providers_list)

@auth_bp.route("/login/<provider_name>")
def oauth_login(provider_name):
    if Config.USE_OAUTH2_PROXY:
        return "Not applicable when using oauth2-proxy", 400

    providers = load_oauth_providers(oauth)
    if provider_name not in providers:
        return "Unsupported provider", 400

    redirect_uri = url_for("auth.authorize", provider_name=provider_name, _external=True)
    return oauth.create_client(provider_name).authorize_redirect(redirect_uri)

@auth_bp.route("/authorize/<provider_name>")
def authorize(provider_name):
    if Config.USE_OAUTH2_PROXY:
        return "Not applicable when using oauth2-proxy", 400

    providers = load_oauth_providers(oauth)
    if provider_name not in providers:
        return "Unsupported provider", 400

    client = oauth.create_client(provider_name)
    token = client.authorize_access_token()
    user_info = client.userinfo()
    session["user"] = user_info
    return redirect(url_for("proxy.dashboard"))

@auth_bp.route("/logout")
def logout():
    """
    Logs out the user from the internal session if not using oauth2-proxy.
    """
    session.pop("user", None)
    if Config.USE_OAUTH2_PROXY:
        return redirect("/oauth2/sign_out")
    return redirect(url_for("auth.login"))
