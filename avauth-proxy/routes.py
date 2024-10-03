# avauth-proxy/routes.py

import os
import uuid
import datetime
from flask import render_template, redirect, url_for, session, request
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from prometheus_client import generate_latest, Counter, Gauge, make_wsgi_app

from . import app, oauth, oauth_providers
from .config import Config
from .utils import (
    load_proxies,
    save_proxies,
    generate_nginx_configs,
    log_event,
    get_available_templates,
    load_events,
)

# Prometheus metrics
num_proxies = Gauge('num_proxies', 'Number of active proxies')
auth_user_count = Gauge('auth_user_count', 'Number of authenticated users')
auth_failures = Counter('auth_failures', 'Number of failed authentication attempts')
event_counter = Counter('event_count', 'Number of events in the log')

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

@app.route('/login')
def login():
    providers = oauth_providers.values()
    return render_template('login.html', providers=providers)

@app.route('/login/<provider_name>')
def oauth_login(provider_name):
    if provider_name not in oauth_providers:
        return "Unsupported provider", 400
    redirect_uri = url_for('authorize', provider_name=provider_name, _external=True)
    return oauth.create_client(provider_name).authorize_redirect(redirect_uri)

@app.route('/authorize/<provider_name>')
def authorize(provider_name):
    if provider_name not in oauth_providers:
        return "Unsupported provider", 400
    try:
        client = oauth.create_client(provider_name)
        token = client.authorize_access_token()
        user_info = client.userinfo()
        session['user'] = user_info
        auth_user_count.inc()
        return redirect(url_for('dashboard'))
    except Exception as e:
        auth_failures.inc()
        return f"Authentication failed: {e}"

@app.route('/logout')
def logout():
    session.pop('user', None)
    auth_user_count.dec()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.remote_addr != '127.0.0.1':
        return "Access denied", 403
    proxies = load_proxies()
    templates = get_available_templates()
    num_proxies.set(len(proxies))
    return render_template('dashboard.html', proxies=proxies, templates=templates)

@app.route('/add_proxy', methods=['POST'])
def add_proxy():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.remote_addr != '127.0.0.1':
        return "Access denied", 403
    service_name = request.form['service_name']
    url_ = request.form['url']
    port = request.form['port']
    template = request.form['template']
    custom_directives = request.form.get('custom_directives', '')
    proxies = load_proxies()
    proxies.append({
        'service_name': service_name,
        'url': url_,
        'port': port,
        'template': template,
        'custom_directives': custom_directives
    })
    save_proxies(proxies)
    generate_nginx_configs(proxies)
    log_event(f"Added new proxy for service {service_name}", 'add')
    return redirect(url_for('dashboard'))

@app.route('/remove_proxy', methods=['POST'])
def remove_proxy():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.remote_addr != '127.0.0.1':
        return "Access denied", 403
    service_name = request.form['service_name']
    proxies = load_proxies()
    proxies = [p for p in proxies if p['service_name'] != service_name]
    save_proxies(proxies)
    config_path = os.path.join(Config.NGINX_CONFIG_DIR, f"{service_name}.conf")
    if os.path.exists(config_path):
        os.remove(config_path)
    generate_nginx_configs(proxies)
    log_event(f"Removed proxy for service {service_name}", 'remove')
    return redirect(url_for('dashboard'))

@app.route('/refresh_proxies', methods=['POST'])
def refresh_proxies():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.remote_addr != '127.0.0.1':
        return "Access denied", 403
    proxies = load_proxies()
    generate_nginx_configs(proxies)
    log_event("Manually refreshed proxies", 'refresh')
    return redirect(url_for('dashboard'))

@app.route('/status')
def status():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.remote_addr != '127.0.0.1':
        return "Access denied", 403
    proxies = load_proxies()
    events = load_events()
    return render_template('status.html', proxies=proxies, events=events)

@app.route('/metrics')
def metrics():
    return generate_latest()

app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {'/metrics': make_wsgi_app()})
