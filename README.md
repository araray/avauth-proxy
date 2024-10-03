# OAuth2 Authentication Proxy Solution with Web UI and Service Management

## Overview

This project extends the OAuth2-proxy functionality by adding a web-based user interface (UI) that allows administrators to manage and configure proxy rules for internal services.

## Features

- OAuth2-based Authentication with multiple providers.
- Web UI for proxy management.
- Event logging and status page.
- Prometheus metrics for monitoring.
- Nginx integration with dynamic configuration templates.

## Setup Instructions

### Prerequisites

- Docker and Docker Compose installed.
- OAuth credentials for the providers you intend to use.

### Configuration

1. **Update `config.toml`:**

   - Replace placeholder client IDs and secrets with your actual OAuth credentials.
   - Customize the application settings if necessary.

2. **Set Up Nginx Configuration:**

   - Ensure that `./nginx/nginx.conf` is properly configured to include proxy configurations from `/etc/nginx/conf.d/proxies/`.

### Running the Application

1. **Build and Run with Docker Compose:**

   ```bash
   docker-compose build
   docker-compose up
