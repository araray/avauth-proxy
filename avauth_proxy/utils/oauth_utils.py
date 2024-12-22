from avauth_proxy.utils.config_utils import get_oauth_providers

def load_oauth_providers(oauth):
    """
    Register OAuth providers dynamically, with special handling for OpenID Connect.
    """
    providers_config = get_oauth_providers()
    oauth_providers = {}

    for provider in providers_config:
        name = provider["name"]
        client_kwargs = provider.get("client_kwargs", {})

        # Special handling for Google and other OpenID Connect providers
        if name == "google":
            oauth.register(
                name=name,
                server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
                client_id=provider["client_id"],
                client_secret=provider["client_secret"],
                client_kwargs=client_kwargs
            )
        else:
            # Traditional OAuth2 registration for other providers
            oauth.register(
                name=name,
                client_id=provider["client_id"],
                client_secret=provider["client_secret"],
                access_token_url=provider.get("access_token_url"),
                authorize_url=provider.get("authorize_url"),
                api_base_url=provider.get("api_base_url"),
                client_kwargs=client_kwargs
            )

        oauth_providers[name] = provider

    return oauth_providers
