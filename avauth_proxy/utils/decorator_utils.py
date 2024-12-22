from functools import wraps
from flask import request
from avauth_proxy.utils.logging_utils import log_configuration_on_error
from config_utils import get_app_config

def log_route_error():
    """
    A decorator that adds configuration logging to route handlers.
    It captures errors and logs them along with relevant configuration details.
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # Get the route name for better error context
            route_name = f.__name__
            try:
                return f(*args, **kwargs)
            except Exception as e:
                # Get configuration for logging
                config = get_app_config()

                # Extract useful request information
                request_info = {
                    'route': request.path,
                    'method': request.method,
                    'args': dict(request.args),
                    # Don't log form data as it might contain sensitive information
                    'headers': dict(request.headers)
                }

                # Add request info to the config for logging
                config['request_info'] = request_info

                # Log the error with full details
                log_configuration_on_error(
                    f"Error in {route_name}: {str(e)}",
                    config,
                    # Pass provider_name if it exists in the kwargs
                    kwargs.get('provider_name')
                )

                # Re-raise the exception to maintain the original error handling
                raise
        return wrapped
    return decorator
