# AVauth-Proxy

## Overview

AVauth-Proxy dynamically manages Nginx reverse proxies and integrates with OAuth2 authentication.
It can use external `oauth2-proxy` or handle OAuth internally with Authlib providers.

**Key Features**:
- Dynamic management of backends via a Flask admin dashboard.
- Supports both `oauth2-proxy` (external) or internal OAuth.
- Configuration-driven: uses TOML config files.
- Integration with Prometheus for metrics.

**Architecture**:
- **Flask App**: Admin UI, dynamically generates Nginx configs.
- **Nginx**: SSL termination, reverse proxy, optional OAuth auth_request.
- **OAuth2**: Either `oauth2-proxy` or internal OAuth (Google, Microsoft, Mock).

## Quick Start

  ```bash
  make build
  make up
  ```

  - Then open `https://YOUR_DOMAIN/dashboard` or `http://localhost:5001/dashboard` (depending on your config) to manage proxies.

  - For detailed instructions, see USAGE.md.

## Testing

  - Use the test environment to ensure everything works:
    ```bash
    make test
    ```
    > This spins up a test environment with a mock OAuth2 server and runs integration tests.

## Switching Auth Modes

  - Edit `config.toml`:
    - `use_oauth2_proxy = true` uses external oauth2-proxy
    - `use_oauth2_proxy = false` uses internal OAuth

  - Rebuild and restart to apply changes.

## Contributing

  Contributions are welcome! Improve documentation, add new tests, or submit patches to enhance features or bugfixes.

## License

  MIT License. See [LICENSE](LICENSE.md) for details.
