# USAGE

## 1. Running the Application

1. **Clone the Repository**:

    ```bash
    git clone https://github.com/<YOUR_USERNAME>/avauth-proxy.git
    cd avauth-proxy
    ```

2. **Configure `config.toml`**:

    - Define your secret key, admin emails, and whether you’re using external or internal OAuth:

        ```toml
        [app]
        secret_key = "some-secret-key"
        admin_emails = ["admin@yourdomain.com"]
        
        [auth]
        use_oauth2_proxy = false  # true if you want external oauth2-proxy
        
        [[oauth_providers]]
        name = "google"
        client_id = "YOUR_GOOGLE_CLIENT_ID"
        client_secret = "YOUR_GOOGLE_CLIENT_SECRET"
        authorize_url = "https://accounts.google.com/o/oauth2/auth"
        access_token_url = "https://oauth2.googleapis.com/token"
        api_base_url = "https://www.googleapis.com/oauth2/v1/"
        client_kwargs = { scope = "openid email profile" }
        label = "Sign in with Google"
        image_url = "https://developers.google.com/identity/images/g-logo.png"
        ```

3. **Build and Launch**:

    ```bash
    make build
    make up
    ```

    - By default, it will start:
        - The Flask app (port 5000 internally, usually mapped to 5001 externally).
        - Nginx on ports 80 and 443.
        - (Optional) oauth2-proxy container if `use_oauth2_proxy = true`.

4. **Access the App**:

    - In your browser, go to `https://<YOUR_DOMAIN>/proxy/dashboard`.
    - If using **internal** OAuth, you will be prompted to log in at `/auth/login`.
    - If using **external** OAuth2-Proxy, Nginx will redirect you to `/oauth2/sign_in` (handled by the oauth2-proxy container).

------

## 2. Configuring Services (Proxies)

### 2.1. Dashboard Approach

1. **Open the Dashboard**:
    - Navigate to `https://<YOUR_DOMAIN>/proxy/dashboard`.
    - If you haven’t configured any proxies yet, you’ll see an empty table.
2. **Add a New Proxy**:
    - Fill out the form:
        - **Service Name** (e.g. `myapp`)
        - **URL/IP** (e.g. `10.0.0.5`)
        - **Port** (e.g. `8080`)
        - **Template** (choose among the available `.j2` templates—`oauth2_disabled.conf.j2`, `default.conf.j2`, etc.)
        - **Auth Required** (checkbox if you want the user to be logged in)
        - **Allowed Emails** (comma-separated email addresses)
        - **Allowed Domains** (comma-separated domain names)
        - **Custom Directives** (any extra lines of Nginx config)
    - Click **Add Proxy**.
3. **Confirm**:
    - The proxy will appear in the “Current Proxies” table.
    - AVauth-Proxy dynamically writes an Nginx config in `/etc/nginx/conf.d/proxies/<service_name>.conf` and reloads Nginx.
4. **Remove a Proxy**:
    - Under “Current Proxies,” click **Remove** next to a service. The Nginx config for that service is removed, and Nginx is reloaded.

### 2.2. TOML/Config File Approach

Alternatively, you can define proxies in `proxies_config.toml`:

```toml
[[proxies]]
service_name = "myapp"
url = "10.0.0.5"
port = "8080"
template = "oauth2_disabled.conf.j2"
auth_required = true
allowed_emails = ["admin@yourdomain.com"]
allowed_domains = ["yourcompany.com"]
custom_directives = ""
```

On startup, AVauth-Proxy will read these proxies, generate the Nginx config, and reload. This is more static but works well for initial bootstrap. Changes can still be made via the dashboard afterward.

------

## 3. Authentication Modes

### 3.1. Internal OAuth with Authlib

- Set `use_oauth2_proxy = false` in `config.toml`.
- When you visit `https://<YOUR_DOMAIN>/auth/login`, you’ll see a login page with the configured providers (Google, Microsoft, etc.).
- On successful OAuth sign-in, user data is placed in `session["user"]` (email, name, etc.).
- If a proxy is marked `auth_required = true`, Nginx calls `/auth/validate/<service_name>` to ensure the user is logged in and whitelisted.

### 3.2. External oauth2-proxy

- Set `use_oauth2_proxy = true`.

- The `oauth2-proxy` container handles the entire login flow.

- The Flask app is typically used only for admin/dash tasks or for generating Nginx config.

- The Nginx config for each auth-required service does:

    ```nginx
    auth_request /oauth2/auth;
    error_page 401 = /oauth2/sign_in;
    ```

- `oauth2_proxy` can be configured for email whitelisting if desired.

------

## 4. Routing Methods (Subdomains vs. Paths)

### 4.1. Subdomain-Based

- Each service is served at `<service_name>.paranoid.land`.
- In your proxy definition, set `server_name = "myapp.paranoid.land"` instead of a path-based approach.
- Typically you’ll use a wildcard certificate for `*.paranoid.land`.

### 4.2. Path-Based

- You define `location /myapp/ { ... }` in Nginx for each service.

- The dashboard or config can store 

    ```
    service_name = "myapp"
    ```

    , and AVauth-Proxy injects something like:

    ```nginx
    location /myapp {
        {% if auth_required %}
        auth_request /auth/validate/myapp;
        ...
        {% endif %}
        proxy_pass http://10.0.0.5:8080;
    }
    ```

Either approach can be done by editing or creating the appropriate `.j2` templates under `nginx_templates/`.

------

## 5. Admin-Only Dashboard Access

You can restrict the entire `/proxy/` blueprint to “admin emails”:

1. **Set `admin_emails`** in `config.toml` under `[app]`.

2. In `proxy_routes.py`

    , a 

    ```
    before_request
    ```

     hook checks if:

    ```python
    if "user" not in session:
        return redirect(url_for("auth.login"))
    user_email = session["user"].get("email")
    if user_email not in Config.ADMIN_EMAILS:
        return "Forbidden", 403
    ```

3. Only emails in that list can add/remove proxies or see the dashboard.

------

## 6. Observing Metrics & Logs

1. **Prometheus Metrics** at `/metrics` (Nginx proxies to the Flask route which returns `prometheus_client` data).
2. **Nginx logs**: Docker container logs (e.g., `docker logs <nginx_container>`).
3. **Flask/Gunicorn logs**: `docker logs <app_container>` for real-time debug.
4. **Events Log**: The project logs events (like “Added new proxy” or “Removed proxy”) to a JSON file (by default `logs/events.log`), if configured.

------

## 7. Testing & Development

1. Local Tests:

    ```bash
    make test
    ```

    - Spins up a test environment (via `docker-compose_test.yaml`) with a mock OAuth2 server.

2. Test Coverage:

    ```bash
    make coverage
    ```

    - Runs pytest with coverage, showing coverage reports.

3. Manual End-to-End:

    - Bring up the system: `make up`.
    - Visit `https://<YOUR_DOMAIN>/proxy/dashboard`.
    - Add a new backend.
    - Confirm you can or cannot access it, depending on `auth_required`.

------

## 8. Common Gotchas

- **500 at `/`:** Make sure you have a valid return in your root route if `use_oauth2_proxy` is `true`.
- **Missing domain in Google OAuth**: Ensure your OAuth callback URIs match `https://<YOUR_DOMAIN>/auth/authorize/google`.
- **Docker healthcheck fails** if the root route returns 500 or if the container can’t resolve internal paths. You can adjust the healthcheck path in the Dockerfile or `docker-compose.yaml` if needed.
- **SSL Certificates**: For production, place your valid certs in `./ssl/fullchain.pem` and `./ssl/privkey.pem`.
- **Subdomain vs. Path**: Make sure your templates reflect how you want to route.

------

## 9. Changing Authentication Mode

1. Switching from internal to external:
    - In `config.toml`, set `use_oauth2_proxy = true`.
    - Bring up the `oauth2_proxy` container in `docker-compose.yaml`.
    - Adjust your Nginx templates to call `auth_request /oauth2/auth;` instead of calling `/auth/validate/<service_name>`.
2. Back to internal:
    - Set `use_oauth2_proxy = false`.
    - Remove or comment out the `oauth2_proxy` container from `docker-compose.yaml`.
    - Nginx templates use `oauth2_disabled.conf.j2` or similar, and call the internal route for validation.

------

## 10. Advanced Topics

- **User Whitelists**: If you want to store them in a DB or a separate config, you can enhance the `validate` route.
- **Roles & Permissions**: Extend the internal logic to have role-based controls beyond “admin vs. not admin.”
- **CI/CD**: Integrate `make test` into your pipeline so you can verify changes before deploying.
- **Performance Tuning**: Adjust Gunicorn workers, concurrency, and Nginx worker_processes for heavy loads.

------

## Summary

With `AVauth-Proxy`, you can quickly spin up a reverse-proxy setup that supports:

- **Multiple backends** (added dynamically)
- **Optional OAuth-based authentication** (internal or external)
- **Flexible routing** by subdomain or path
- **Easy admin control** for adding or removing proxies
- **Selective user whitelists** to tighten security

Refer to this `USAGE.md` any time you need reminders on how to configure and operate AVauth-Proxy in different modes. For deeper architecture details and contribution guidelines, see README.md. Happy proxying!
