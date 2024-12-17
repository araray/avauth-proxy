import os
import subprocess
from jinja2 import Environment, FileSystemLoader
from avauth_proxy.config import Config

def generate_nginx_configs(proxies):
    """
    Generates Nginx configuration files from templates, selecting the appropriate template
    based on whether oauth2-proxy is used or not.
    """
    nginx_templates_dir = Config.NGINX_TEMPLATES_DIR
    nginx_config_dir = Config.NGINX_CONFIG_DIR
    temp_dir = f"{nginx_config_dir}.temp"

    # Ensure directories exist
    os.makedirs(temp_dir, exist_ok=True)

    env = Environment(loader=FileSystemLoader(nginx_templates_dir))
    # Decide default template based on auth mode
    default_template_name = "default.conf.j2" if Config.USE_OAUTH2_PROXY else "oauth2_disabled.conf.j2"

    try:
        for proxy in proxies:
            template_name = proxy.get("template", default_template_name)
            template = env.get_template(template_name)

            config_content = template.render(
                service_name=proxy.get("service_name", "default"),
                url=proxy.get("url", "localhost"),
                port=proxy.get("port", 80),
                custom_directives=proxy.get("custom_directives", "")
            )

            config_path = os.path.join(temp_dir, f"{proxy['service_name']}.conf")
            with open(config_path, "w") as f:
                f.write(config_content)

        # Clean old
        for filename in os.listdir(nginx_config_dir):
            os.remove(os.path.join(nginx_config_dir, filename))
        for filename in os.listdir(temp_dir):
            os.rename(os.path.join(temp_dir, filename), os.path.join(nginx_config_dir, filename))

        reload_nginx()
    except Exception as e:
        raise RuntimeError(f"Failed to generate Nginx configs: {e}")
    finally:
        for filename in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, filename))
        os.rmdir(temp_dir)

def reload_nginx():
    result = subprocess.run(["nginx", "-s", "reload"], capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"Nginx reload failed: {result.stderr.decode('utf-8')}")
