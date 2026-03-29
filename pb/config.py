def resolve_cohere_api_key(explicit_key, env_key):
    if explicit_key:
        return explicit_key.strip()

    if env_key:
        return env_key.strip()

    return ""


def resolve_requests_per_minute(value):
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    try:
        parsed = int(text)
    except ValueError:
        return None

    if parsed <= 0:
        return None

    return parsed
