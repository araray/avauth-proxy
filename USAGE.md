# USAGE

## Running the Application

1. **Configure the Application**:
   - Update `config.toml` with your OAuth providers, SSL certificates (for nginx), and whether to use `oauth2-proxy` or internal OAuth.

2. **Build and Run**:
  ```bash
   make build
   make up
  ```
  This will start:

  - The Flask app (admin UI and dynamic configuration generator).
  - Nginx (serving requests, doing SSL termination, and optionally using oauth2-proxy).
  - OAuth2-proxy (if use_oauth2_proxy is set to true in config).
  - Mock OAuth server (if needed for testing).

3. **Access the Admin Dashboard**:
  - If using `oauth2-proxy`: Visit `https://YOUR_DOMAIN/dashboard` (after authenticating).
  - If using internal OAuth: Visit [http://localhost:5001/dashboard](http://localhost:5001/dashboard) and login with one of the configured providers.

4. **Managing Proxies**:
  - On the dashboard, add new backend services by specifying service_name, url, port, and template.
  - Removing proxies updates Nginx configuration dynamically.

## Testing

  1. Run Tests:
    - Ensure the test environment is up:
      ```bash
      make test-env-up
      ```
    - Run tests with coverage:
      ```bash
      make test
      ```
    Test results and coverage report will be displayed.

  2. Integration Tests:
    - The mock OAuth2 server and `docker-compose_test.yaml` environment ensure integration tests run automatically.

  3. Cleaning Up:
    ```bash
    make clean
    ```

## Changing Authentication Mode

  - To switch from `oauth2-proxy` to internal OAuth authentication:
    - In `config.toml`, set `use_oauth2_proxy = false`.
    - Rebuild and restart the containers.

## Advanced Configuration

  - For custom templates, place them in `avauth_proxy/nginx_templates/`.
  - For SSL, place certificates in `./ssl/` and update `nginx/nginx.conf`.
  - OAuth providers can be added/removed in `config.toml`.
