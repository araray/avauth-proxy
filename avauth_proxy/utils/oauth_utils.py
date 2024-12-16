import tomllib
from avauth_proxy.config import Config
from avauth_proxy.utils.config_utils import get_oauth_providers

def load_oauth_providers(oauth):
    providers_config = get_oauth_providers()
    oauth_providers = {}
    for provider in providers_config:
        oauth.register(
            name=provider["name"],
            client_id=provider["client_id"],
            client_secret=provider["client_secret"],
            access_token_url=provider["access_token_url"],
            authorize_url=provider["authorize_url"],
            api_base_url=provider["api_base_url"],
            client_kwargs=provider.get("client_kwargs", {})
        )
        oauth_providers[provider["name"]] = provider
    return oauth_providers
