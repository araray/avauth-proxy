from flask import Blueprint, render_template, session, request, redirect, url_for
from avauth_proxy.utils.oauth_utils import load_oauth_providers
from avauth_proxy.utils.logging_utils import log_configuration_on_error, log_event
from avauth_proxy.utils.decorator_utils import log_route_error
from avauth_proxy.config import Config
from avauth_proxy import oauth
from avauth_proxy.models import get_db, User
from avauth_proxy.utils.security_utils import hash_password, check_password
from sqlalchemy.exc import NoResultFound



auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login")
@log_route_error()
def login():
    """Display login page if internal OAuth is enabled."""
    if Config.USE_OAUTH2_PROXY:
        return redirect("/oauth2/sign_in")

    # If local_auth is enabled, show local auth form
    app_config = Config.app_config
    local_auth_enabled = app_config["local_auth"].get("enabled", False)

    providers = load_oauth_providers(oauth)
    providers_list = providers.values()

    return render_template("auth/login.html", providers=providers_list, local_auth_enabled=local_auth_enabled)

@auth_bp.route("/login/local", methods=["POST"])
@log_route_error()
def login_local():
    """
    Handle local username/password authentication.
    """
    app_config = Config.app_config
    if not app_config["local_auth"].get("enabled", False):
        return "Local auth not enabled", 400

    email = request.form.get("email")
    password = request.form.get("password")

    if not email or not password:
        return "Missing credentials", 400

    db_generator = get_db()
    db = next(db_generator)
    try:
        user = db.query(User).filter(User.email == email).one()
    except NoResultFound:
        return "Invalid email or password", 401

    if not check_password(password, user.password_hash):
        return "Invalid email or password", 401

    # Auth success
    session["user"] = {"email": user.email}
    log_event(f"User {user.email} logged in locally.", "auth_success")
    return redirect(url_for("proxy.dashboard"))

@auth_bp.route("/signup/local", methods=["GET", "POST"])
@log_route_error()
def signup_local():
    """
    Simple signup flow for local auth.
    """
    app_config = Config.app_config
    if not app_config["local_auth"].get("enabled", False):
        return "Local auth not enabled", 400

    if request.method == "GET":
        return render_template("auth/signup.html")

    email = request.form.get("email")
    password = request.form.get("password")
    if not email or not password:
        return "Missing email or password", 400

    db_generator = get_db()
    db = next(db_generator)
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        return "User already exists", 400

    new_user = User(email=email, password_hash=hash_password(password))
    db.add(new_user)
    db.commit()
    log_event(f"New user {email} signed up locally.", "user_signup")
    return redirect(url_for("auth.login"))

@auth_bp.route("/login/<provider_name>")
@log_route_error()
def oauth_login(provider_name):
    if Config.USE_OAUTH2_PROXY:
        return "Not applicable when using oauth2-proxy", 400

    providers = load_oauth_providers(oauth)
    if provider_name not in providers:
        return "Unsupported provider", 400

    redirect_uri = url_for("auth.authorize", provider_name=provider_name, _external=True)
    return oauth.create_client(provider_name).authorize_redirect(redirect_uri)

@auth_bp.route("/authorize/<provider_name>")
@log_route_error()
def authorize(provider_name):
    if Config.USE_OAUTH2_PROXY:
        return "Not applicable when using oauth2-proxy", 400

    providers = load_oauth_providers(oauth)
    if provider_name not in providers:
        return "Unsupported provider", 400

    client = oauth.create_client(provider_name)
    try:
        token = client.authorize_access_token()

        # For Google (OpenID Connect), we don't need to make a separate userinfo call
        if provider_name == "google":
            user_info = token.get('userinfo')
            if not user_info:
                user_info = client.parse_id_token(token)
        else:
            user_info = client.userinfo()

        session["user"] = user_info
        log_event(f"Successful login for provider {provider_name}", "auth_success")
        return redirect(url_for("proxy.dashboard"))
    except Exception as e:
        # Get the full configuration for logging
        config = get_app_config()

        # Log the error with full configuration details
        log_configuration_on_error(e, config, provider_name)

        error_message = f"Authorization failed for {provider_name}: {str(e)}"
        return error_message, 400

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
