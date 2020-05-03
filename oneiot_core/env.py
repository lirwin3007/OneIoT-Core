import os

defaults = {
    "ONEIOT_C_PORT": 1102,
    "ONEIOT_C_STATIC_IP": "192.168.4.1",
    "ONEIOT_C_NETWORK_INTERFACE": "wlan0",
    "ONEIOT_C_NETWORK_SSID": "OneIoT",
}

def var(name, default=None):
    if default == None:
        if name in defaults:
            default = defaults[name]
    return os.getenv(name) if os.getenv(name) is not None else default

def network_password():
    config = open("/etc/hostapd/hostapd.conf").read()
    for line in config.split("\n"):
        parts = line.split("=")
        if parts[0] == "wpa_passphrase":
            return parts[1]
    return None
