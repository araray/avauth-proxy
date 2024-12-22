import os
import uuid
import datetime
import logging
import json

from pythonjsonlogger.json import JsonFormatter
from avauth_proxy.config import Config
from copy import deepcopy

def configure_logging():
    os.makedirs(os.path.dirname(Config.EVENTS_LOG_FILE), exist_ok=True)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    log_handler = logging.FileHandler(Config.EVENTS_LOG_FILE)
    formatter = JsonFormatter()
    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)

def log_event(description, code):
    event_id = str(uuid.uuid4())
    timestamp = datetime.datetime.now().isoformat()
    logging.info({"event_id": event_id, "timestamp": timestamp, "description": description, "code": code})

def sanitize_config(config):
    """
    Creates a safe copy of configuration for logging by removing sensitive information.

    This function makes a deep copy of the configuration and replaces sensitive values
    with placeholders to ensure we don't accidentally log credentials.
    """
    # Make a deep copy so we don't modify the original config
    safe_config = deepcopy(config)

    # List of keys that contain sensitive information
    sensitive_keys = {'client_secret', 'secret_key', 'cookie_secret', 'password'}

    def redact_sensitive_values(obj):
        """Recursively redacts sensitive values in a dictionary structure."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if any(sensitive in key.lower() for sensitive in sensitive_keys):
                    obj[key] = '**REDACTED**'
                else:
                    redact_sensitive_values(value)
        elif isinstance(obj, list):
            for item in obj:
                redact_sensitive_values(item)
        return obj

    return redact_sensitive_values(safe_config)

def log_configuration_on_error(error_message, config, provider_name=None):
    """
    Logs an error along with relevant configuration details.

    This function creates a structured log entry that includes:
    - The error message
    - The provider configuration (if specified)
    - General application configuration
    - Authentication settings
    """
    try:
        # Create a structured log entry
        log_entry = {
            'error': str(error_message),
            'timestamp': datetime.datetime.now().isoformat(),
            'event_type': 'configuration_error',
        }

        # Add provider-specific configuration if a provider was specified
        if provider_name and 'oauth_providers' in config:
            provider_config = next(
                (p for p in config.get('oauth_providers', [])
                 if p.get('name') == provider_name),
                None
            )
            if provider_config:
                log_entry['provider_config'] = sanitize_config(provider_config)

        # Add general configuration settings
        log_entry['app_config'] = sanitize_config({
            'use_oauth2_proxy': config.get('auth', {}).get('use_oauth2_proxy'),
            'session_cookie_secure': config.get('app', {}).get('session_cookie_secure'),
            'session_cookie_httponly': config.get('app', {}).get('session_cookie_httponly'),
            'session_cookie_samesite': config.get('app', {}).get('session_cookie_samesite'),
        })

        # Format the log entry as a pretty-printed JSON string for readability
        formatted_log = json.dumps(log_entry, indent=2)

        # Use the existing logging mechanism
        log_event(
            f"Configuration Error Details:\n{formatted_log}",
            "config_error"
        )

    except Exception as logging_error:
        # If something goes wrong while logging, we should know about it
        log_event(
            f"Failed to log configuration: {str(logging_error)}",
            "logging_error"
        )
