from flask import Blueprint, render_template, session, redirect, url_for, current_app
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
    try:
        token = client.authorize_access_token()

        # For OpenID Connect providers like Google
        if "id_token" in token:
            user_info = client.parse_id_token(token)
        else:
            # Fallback to userinfo endpoint for regular OAuth2
            user_info = client.userinfo()

        session["user"] = user_info
        return redirect(url_for("proxy.dashboard"))
    except Exception as e:
        # Log the error for debugging
        current_app.logger.error(f"Authorization failed: {str(e)}")
        return f"Authorization failed: {str(e)}", 400

@auth_bp.route("/logout")
def logout():
    """
    Logs out the user from the internal session if not using oauth2-proxy.
    """
    session.pop("user", None)
    if Config.USE_OAUTH2_PROXY:
        return redirect("/oauth2/sign_out")
    return redirect(url_for("auth.login"))

@auth_bp.route("/validate/<service_name>")
def validate_service(service_name):
    """
    This is called by Nginx 'auth_request' to check if the user is logged in
    and if they're allowed for this particular service.
    Return 200 if allowed, 401 or 403 if not.
    """
    from avauth_proxy.utils.file_utils import load_proxies
    proxies = load_proxies()

    # Find the matching service config
    service = next((p for p in proxies if p["service_name"] == service_name), None)
    if not service:
        # If service not found, deny
        return "", 403

    # Check if the user is in Flask session
    if "user" not in session:
        # Not logged in => return 401
        return "", 401

    user_info = session["user"]  # e.g., user_info["email"]
    user_email = user_info.get("email")

    # If service has auth_required == false, then 200
    if not service.get("auth_required", False):
        return "", 200

    # If service has a list of allowed_emails
    allowed_emails = service.get("allowed_emails", [])
    allowed_domains = service.get("allowed_domains", [])

    # If the user email is in allowed_emails => OK
    if user_email in allowed_emails:
        return "", 200

    # Or if domain is in allowed_domains
    user_domain = user_email.split("@")[-1] if user_email else ""
    if user_domain in allowed_domains:
        return "", 200

    # Otherwise 403
    return "", 403
