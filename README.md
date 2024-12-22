# AVauth-Proxy

## Overview

**AVauth-Proxy** is a dynamic reverse-proxy manager built on Flask + Nginx, providing optional OAuth2 authentication (either via an external `oauth2-proxy` or internally using Authlib). It’s designed to manage multiple backend services—some of which can be open (no auth) and others restricted (OAuth login, email/domain whitelists). Additionally, it offers an **admin dashboard** to configure new proxies on-the-fly while restricting critical actions to specific admin emails.

### Key Features

1. **Dynamic Proxy Management**
    - Add or remove backend services via a Flask-based admin dashboard.
    - Nginx configs are automatically generated and reloaded in real time.
2. **Authentication Modes**
    - **External**: use an existing `oauth2-proxy` container (set `use_oauth2_proxy = true` in `config.toml`).
    - **Internal**: rely on Authlib with providers (Google, Microsoft, Mock, etc.)—set `use_oauth2_proxy = false`.
3. **Access Control**
    - Some services can be publicly accessible (no login required).
    - Others can require authentication; you can specify whitelists of allowed emails or domains.
    - Admin dashboard routes are restricted to configured “admin” emails, preventing unauthorized modifications.
4. **Flexible Routing**
    - Subdomain-based: e.g., `SERVICE_NAME.paranoid.land`.
    - Path-based: e.g., `paranoid.land/SERVICE_NAME`.
         In either approach, Nginx is configured to route requests to the correct backend while optionally enforcing authentication.
5. **Monitoring / Metrics**
    - Prometheus metrics endpoint at `/metrics`.

------

## Architecture

```
+-------------+                 +------------------------------------+
|  Web Client |  --->  443/HTTPS|    Nginx (SSL, Reverse Proxy)       |
+-------------+                 |  - Dynamically includes conf files  |
                                |  - Optionally calls /auth/validate/<service>
                                +------------------------------------+
                                                |
                                                v
                                   +-------------------------------+
                                   | Flask (Admin & OAuth logic)  |
                                   |  - Admin Dashboard            |
                                   |  - Authlib or external oauth2-proxy
                                   |  - Validate requests & whitelists
                                   +-------------------------------+
                                                |
                                                v
                                   +-------------------------------+
                                   |  One or Many Backend Services |
                                   |  (public or restricted)       |
                                   +-------------------------------+
```

1. **Nginx**:
    - Terminates SSL on port 443.
    - If a service’s config has `auth_required = true`, Nginx calls the internal `auth_request /auth/validate/<service_name>` route to confirm the user is logged in and whitelisted.
    - Passes authorized traffic to the correct backend.
2. **Flask (the AVauth-Proxy app)**:
    - Provides the Admin Dashboard, letting you add or remove proxies (services).
    - Handles internal OAuth flows or delegates to an external `oauth2-proxy`.
    - Manages the session and user info if using internal OAuth.
    - Enforces an admin-only policy for critical routes like `/proxy/dashboard` or `/proxy/add_proxy`.
3. **Backends**:
    - Could be any HTTP service.
    - The user can choose “auth_required = false” (public) or “auth_required = true” (login + optional email/domain white-list).

------

## Quick Start

1. **Clone and Configure**:

    - Clone the repo and update 

        ```
        config.toml
        ```

        :

        ```toml
        [app]
        secret_key = "some-secret-key"
        admin_emails = ["admin@yourdomain.com"]  # Only these can use the admin dashboard
        
        [auth]
        use_oauth2_proxy = false  # or true for external proxy
        
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

2. **Build and Run** (internally):

    ```bash
    make build
    make up
    ```

    - This brings up the Flask app, Nginx, and (optionally) `oauth2-proxy` if `use_oauth2_proxy=true`.

3. **Access the Dashboard**:

    - Go to `https://paranoid.land/proxy/dashboard` (or your domain/port).
    - You’ll be redirected to `/auth/login` if **internal** OAuth is used and you’re not logged in.
    - If you log in with Google (and your email is in the `admin_emails`), you’ll see the admin interface.

------

## Configuring Services (Proxies)

In the admin dashboard (or via `proxies_config.toml`), define each service with:

- **Service Name**: e.g. “myapp”.
- **URL/IP**: e.g. “10.0.0.5”
- **Port**: e.g. “8080”
- **Auth Required**: (true/false)
- **Allowed Emails**: comma-separated emails if you want a specific whitelist.
- **Allowed Domains**: comma-separated domains for domain-based whitelisting.
- **Custom Directives**: optional extra lines for advanced Nginx directives.

**Path-based** routing example:

```toml
[[proxies]]
service_name = "myapp"
url = "10.0.0.5"
port = "8080"
auth_required = true
allowed_emails = ["alice@example.com","bob@example.com"]
allowed_domains = ["mycompany.com"]
template = "oauth2_disabled.conf.j2"  # or "default.conf.j2" if using external oauth2-proxy
```

**Subdomain-based** routing example:

```toml
[[proxies]]
service_name = "blog"
server_name = "blog.paranoid.land"
url = "10.0.0.6"
port = "8000"
auth_required = false
template = "oauth2_disabled.conf.j2"
```

The app then **generates** an Nginx config block for each service, reloading Nginx on the fly.

------

## Authentication & Access Control

### Internal OAuth

- Set `use_oauth2_proxy = false` in `config.toml`.
- The `/auth/login` route shows a list of configured Authlib providers (Google, Microsoft, etc.).
- On success, user info (email, name) is stored in `session["user"]`.

### External oauth2-proxy

- Set `use_oauth2_proxy = true`.
- Nginx “auth_request” calls `oauth2_proxy`, which handles login + whitelisting.
- The Flask app becomes simpler; it does not handle individual OAuth logins.

### Admin Dashboard Protection

- `admin_emails` in `[app]` section of `config.toml` sets who can see or modify proxies.
- The code checks if `session["user"].email` is in that list. Otherwise, returns 403.

### Per-Service Authorization

- If `auth_required = true`, the generated Nginx config calls `/auth/validate/<service_name>` (internal subrequest) to confirm user is logged in + whitelisted.
- If the user’s email is missing, the subrequest returns 401 or 403, blocking the request.

------

## Subdomains vs. Paths

1. **Subdomain**: You can define `server_name = "service.paranoid.land"` in each proxy config, then generate an Nginx `server { ... }` block per service. A wildcard SSL cert (`*.paranoid.land`) is typically used.
2. **Path-based**: Single `server_name paranoid.land;` with location blocks. E.g. `location /myapp { proxy_pass http://10.0.0.5:8080; }`.

**Choose** whichever pattern suits your domain setup. The Jinja2 templates (`default.conf.j2`, `oauth2_disabled.conf.j2`, etc.) can be customized to handle either approach.

------

## Usage Examples

1. **Add a public service**:

    - Go to `/proxy/dashboard`.
    - “Add Proxy”: set `auth_required = false`. Now the service is open to everyone.

2. **Add a private service** with an email whitelist:

    - `auth_required = true`.
    - Fill `allowed_emails` or `allowed_domains`.
    - Nginx will call `/auth/validate/<service_name>` for every request. The route checks if the user’s email is allowed.

3. **Switch from internal to external**:

    - In `config.toml`, set `use_oauth2_proxy = true`.

    - Rebuild + restart containers:

        ```bash
        docker-compose down
        docker-compose up -d --build
        ```

    - Make sure `oauth2-proxy` container is configured to handle sign-ins.

------

## Testing

1. **Local Integration Tests**:

    ```bash
    make test
    ```

    or

    ```bash
    pytest --cov=avauth_proxy --cov-report=term-missing
    ```

    This spins up a test environment (via `docker-compose_test.yaml`), including a mock OAuth2 server.

2. **Manual Testing**:

    - Access `https://YOUR_DOMAIN/proxy/dashboard` → add a service.
    - Confirm logs (`docker logs`) that Nginx config is reloaded.
    - Attempt to visit the newly created subdomain or path. Check the authentication flow if required.

3. **Cleanup**:

    ```bash
    make clean
    ```

    which tears down containers and removes logs.

------

## Contributing

Contributions are welcome! You can:

- **Submit Pull Requests**: whether documentation, bugfixes, new template expansions for advanced Nginx rules, or better access control logic.
- **Add Test Cases**: especially for new OAuth providers, or whitelisting edge cases.
- **Enhance the Dashboard**: for instance, improving the UI for adding multiple domains, or integrating with external secrets managers.

Please open an issue or PR with your improvements, and ensure your changes pass existing tests.

------

## License

Licensed under the MIT License. Feel free to fork or integrate this project into your own environment, subject to the usual MIT terms.

------

## Contact & More Info

- For help or feature requests, open a GitHub issue.
- If you’d like to integrate advanced ACL logic or a full user database, check the code’s `auth_routes.py` and `proxy_routes.py` for extension points.
- For production usage at scale, consider:
    - Dedicated domain patterns or wildcard certificates for subdomains.
    - Secure cookie settings (`SESSION_COOKIE_SECURE=true`, etc.).
    - Hardening Docker images and leveraging `docker-compose` with TLS secrets carefully managed.

With **AVauth-Proxy**, you can dynamically add or remove proxies, require login or not, and unify all your backend services behind an extensible, OAuth-capable gateway!
