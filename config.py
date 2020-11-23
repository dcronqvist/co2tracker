import json

fi = "config.json"

def load_settings():
    with open(fi, "rb") as f:
        s = json.load(f)
        return s
    return None

def get_setting(key, default=None):
    settings = load_settings()
    if key in settings:
        return settings.get(key, default)
    return default
    