import ujson

def load_config(path="config_device.json"):
    """Carga configuración de WiFi y Adafruit IO desde un archivo JSON."""
    with open(path, "r") as f:
        data = ujson.loads(f.read())
    return data
