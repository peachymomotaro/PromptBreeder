def resolve_cohere_api_key(explicit_key, env_key):
    if explicit_key:
        return explicit_key.strip()

    if env_key:
        return env_key.strip()

    return ""
