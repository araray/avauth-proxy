from flask import Blueprint, render_template, request, redirect, url_for, session, abort
from avauth_proxy.utils.file_utils import load_proxies, save_proxies
from avauth_proxy.utils.nginx_utils import generate_nginx_configs
from avauth_proxy.utils.logging_utils import log_event
from avauth_proxy.config import Config
from avauth_proxy.utils import get_available_templates, load_events

proxy_bp = Blueprint("proxy", __name__)

@proxy_bp.before_request
def require_admin():
    # If user not logged in, redirect to login
    if "user" not in session:
        return redirect(url_for("auth.login"))
    user_email = session["user"].get("email")
    # If user_email is not in admin list, 403
    if user_email not in Config.ADMIN_EMAILS:
        return abort(403, "Forbidden: not an admin")

@proxy_bp.route("/dashboard")
def dashboard():
    if Config.USE_OAUTH2_PROXY:
        # External auth - assume Nginx + oauth2-proxy handle it.
        # If not authenticated, oauth2-proxy returns 401.
        # Just show dashboard.
        pass
    else:
        # Internal auth - check session
        if "user" not in session:
            return redirect(url_for("auth.login"))

    proxies = load_proxies()
    templates = get_available_templates()
    return render_template("proxy/dashboard.html", proxies=proxies, templates=templates)

@proxy_bp.route("/add_proxy", methods=["POST"])
def add_proxy():
    """
    Add a new proxy configuration.
    """
    if not Config.USE_OAUTH2_PROXY and "user" not in session:
        return redirect(url_for("auth.login"))

    service_name = request.form["service_name"]
    url_ = request.form["url"]
    port = request.form["port"]
    template = request.form["template"]
    custom_directives = request.form.get("custom_directives", "")

    auth_required_str = request.form.get("auth_required", "false")
    auth_required = auth_required_str.lower() in ("true", "on", "1")

    allowed_emails_str = request.form.get("allowed_emails", "")
    allowed_emails = [e.strip() for e in allowed_emails_str.split(",") if e.strip()]

    allowed_domains_str = request.form.get("allowed_domains", "")
    allowed_domains = [d.strip() for d in allowed_domains_str.split(",") if d.strip()]

    proxies = load_proxies()
    proxies.append({
        "service_name": service_name,
        "url": url_,
        "port": port,
        "template": template,
        "auth_required": auth_required,
        "allowed_emails": allowed_emails,
        "allowed_domains": allowed_domains,
        "custom_directives": custom_directives
    })

    save_proxies(proxies)
    generate_nginx_configs(proxies)
    log_event(f"Added new proxy: {service_name}", "add")
    return redirect(url_for("proxy.dashboard"))

@proxy_bp.route("/remove_proxy", methods=["POST"])
def remove_proxy():
    """
    Remove a proxy configuration.
    """
    if not Config.USE_OAUTH2_PROXY and "user" not in session:
        return redirect(url_for("auth.login"))

    service_name = request.form["service_name"]
    proxies = [p for p in load_proxies() if p["service_name"] != service_name]
    save_proxies(proxies)
    generate_nginx_configs(proxies)
    log_event(f"Removed proxy: {service_name}", "remove")
    return redirect(url_for("proxy.dashboard"))

@proxy_bp.route("/status")
def status():
    """
    Status page showing current proxies and event logs.
    """
    if not Config.USE_OAUTH2_PROXY and "user" not in session:
        return redirect(url_for("auth.login"))

    proxies = load_proxies()
    events = load_events()
    return render_template("proxy/status.html", proxies=proxies, events=events)
