import os
import subprocess
from jinja2 import Environment, FileSystemLoader
from avauth_proxy.config import Config


def generate_nginx_configs(proxies):
    """
    Generates Nginx configuration files for all proxies, using Jinja2 templates.
    Configuration files are created in a temporary directory and then atomically moved
    into the active Nginx configuration directory to ensure consistency.

    :param proxies: List of proxy definitions.
    """
    nginx_templates_dir = Config.NGINX_TEMPLATES_DIR
    nginx_config_dir = Config.NGINX_CONFIG_DIR
    temp_dir = f"{nginx_config_dir}.temp"

    # Ensure directories exist
    os.makedirs(temp_dir, exist_ok=True)

    # Set up the Jinja2 environment
    env = Environment(loader=FileSystemLoader(nginx_templates_dir))

    try:
        # Generate configurations into the temporary directory
        for proxy in proxies:
            template_name = proxy.get("template", "default.conf.j2")
            template = env.get_template(template_name)

            # Render the configuration using template variables
            config_content = template.render(
                service_name=proxy.get("service_name", "default"),
                url=proxy.get("url", "localhost"),
                port=proxy.get("port", 80),
                custom_directives=proxy.get("custom_directives", "")
            )

            # Write the rendered configuration to the temp directory
            config_path = os.path.join(temp_dir, f"{proxy['service_name']}.conf")
            with open(config_path, "w") as f:
                f.write(config_content)

        # Atomically replace the old configuration with the new one
        for filename in os.listdir(nginx_config_dir):
            os.remove(os.path.join(nginx_config_dir, filename))
        for filename in os.listdir(temp_dir):
            os.rename(os.path.join(temp_dir, filename), os.path.join(nginx_config_dir, filename))

        # Reload Nginx to apply new configurations
        reload_nginx()

    except Exception as e:
        raise RuntimeError(f"Failed to generate Nginx configs: {e}")

    finally:
        # Clean up the temporary directory
        for filename in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, filename))
        os.rmdir(temp_dir)


def reload_nginx():
    """
    Reloads the Nginx service to apply the latest configurations.
    Raises an exception if the reload command fails.
    """
    result = subprocess.run(["nginx", "-s", "reload"], capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"Nginx reload failed: {result.stderr.decode('utf-8')}")
