from avauth_proxy.utils.config_utils import get_oauth_providers

def load_oauth_providers(oauth):
    """
    Register OAuth providers dynamically, with special handling for OpenID Connect providers.
    """
    providers_config = get_oauth_providers()
    oauth_providers = {}

    for provider in providers_config:
        client_kwargs = provider.get("client_kwargs", {})
        client_kwargs.setdefault("scope", "openid email profile")

        # Check if this is an OpenID Connect provider
        if "server_metadata_url" in provider:
            # For OpenID Connect, we let Authlib fetch the metadata
            oauth.register(
                name=provider["name"],
                client_id=provider["client_id"],
                client_secret=provider["client_secret"],
                server_metadata_url=provider["server_metadata_url"],
                client_kwargs=client_kwargs
            )
        else:
            # For traditional OAuth2 providers, use explicit endpoints
            oauth.register(
                name=provider["name"],
                client_id=provider["client_id"],
                client_secret=provider["client_secret"],
                access_token_url=provider["access_token_url"],
                authorize_url=provider["authorize_url"],
                api_base_url=provider["api_base_url"],
                client_kwargs=client_kwargs,
            )

        oauth_providers[provider["name"]] = provider

    return oauth_providers
