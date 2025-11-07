import network
import json
import time

CONFIG_PATH = 'wifi_config.json'

def load_wifi_config(path=CONFIG_PATH):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print("Failed to load Wi-Fi config:", e)
        return None

def save_wifi_config(config, path=CONFIG_PATH):
    try:
        with open(path, 'w') as f:
            json.dump(config, f)
        print("Wi-Fi config saved.")
        return True
    except Exception as e:
        print("Failed to save Wi-Fi config:", e)
        return False

def modify_wifi_config(path=CONFIG_PATH, section=None, key=None, value=None):
    config = load_wifi_config(path)
    if not config:
        print("No config found, cannot modify.")
        return False

    if section and key:
        if section in config and key in config[section]:
            config[section][key] = value
        elif section in config:
            config[section][key] = value
        else:
            config[section] = {key: value}
    elif key:
        config[key] = value
    else:
        print("Invalid modification request.")
        return False

def connect_sta(ssid, password, timeout=10000):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    start = time.ticks_ms()
    while not wlan.isconnected() and time.ticks_diff(time.ticks_ms(), start) < timeout:
        time.sleep_ms(200)
    
    if wlan.isconnected():
        print("Connected to STA:", ssid)
        print("STA IP:", wlan.ifconfig()[0])
        return wlan.ifconfig()[0]
    else:
        print("Failed to connect to STA:", ssid)
        return None

def start_ap(ap_name, password):
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=ap_name, password=password)
    ap.ifconfig(('192.168.0.1', '255.255.255.0', '192.168.0.1', '192.168.0.1'))
    print("Access Point started")
    print("AP SSID:", ap_name)
    print("AP IP:", ap.ifconfig()[0])
    return ap.ifconfig()[0]

def setup_wifi(config):
    sta_ip = None
    ap_ip = None

    mode = config.get("mode", "ap")
    ap_conf = config.get("ap", {})
    sta_conf = config.get("sta", {})

    if mode in ("sta", "dual") and sta_conf.get("enabled"):
        sta_ip = connect_sta(sta_conf["ssid"], sta_conf["password"])
    
    if mode in ("ap", "dual"):
        ap_ip = start_ap(ap_conf["ssid"], ap_conf["password"])
    
    return sta_ip or ap_ip
