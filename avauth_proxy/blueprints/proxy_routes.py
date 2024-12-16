import os
from flask import Blueprint, render_template, request, redirect, url_for, session
from avauth_proxy.utils.file_utils import load_proxies, save_proxies
from avauth_proxy.utils.nginx_utils import generate_nginx_configs
from avauth_proxy.utils.logging_utils import log_event
from avauth_proxy.config import Config

proxy_bp = Blueprint("proxy", __name__)

@proxy_bp.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("auth.login"))
    proxies = load_proxies()
    templates = os.listdir(Config.NGINX_TEMPLATES_DIR)
    return render_template("proxy/dashboard.html", proxies=proxies, templates=templates)

@proxy_bp.route("/add_proxy", methods=["POST"])
def add_proxy():
    if "user" not in session:
        return redirect(url_for("auth.login"))
    service_name = request.form["service_name"]
    url_ = request.form["url"]
    port = request.form["port"]
    template = request.form["template"]
    custom_directives = request.form.get("custom_directives", "")

    proxies = load_proxies()
    proxies.append({
        "service_name": service_name,
        "url": url_,
        "port": port,
        "template": template,
        "custom_directives": custom_directives
    })
    save_proxies(proxies)
    generate_nginx_configs(proxies)
    log_event(f"Added new proxy: {service_name}", "add")
    return redirect(url_for("proxy.dashboard"))

@proxy_bp.route("/remove_proxy", methods=["POST"])
def remove_proxy():
    if "user" not in session:
        return redirect(url_for("auth.login"))
    service_name = request.form["service_name"]
    proxies = [p for p in load_proxies() if p["service_name"] != service_name]
    save_proxies(proxies)
    generate_nginx_configs(proxies)
    log_event(f"Removed proxy: {service_name}", "remove")
    return redirect(url_for("proxy.dashboard"))
