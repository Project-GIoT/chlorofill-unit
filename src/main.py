import gc
import time
import json
import network
import socket

import config
from device_manager import DeviceManager
from unit_manager import UnitManager

unit_manager = UnitManager(config.UNIT_ID, config.UNIT_MODEL, config.FW_VERSION)
device_manager = DeviceManager()

def setup_wifi():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)

    unit_config = unit_manager.get_config()
    ap_name = unit_config['name']
    
    ap.config(essid=ap_name, password=config.WIFI_AP_PASSWORD)
    ap.ifconfig(('192.168.0.1', '255.255.255.0', '192.168.0.1', '192.168.0.1'))
    
    if config.DEBUG:
        print('\nUnitAccess Point started')
        print(f'AP IP address   : {ap.ifconfig()[0]}')
        print(f'AP Name         : {ap_name}')
        print(f'AP Password     : {config.WIFI_AP_PASSWORD}')

def send_response(conn, data, status_code=200):
    if isinstance(data, (dict, list)):
        data = json.dumps(data)
    response = f"HTTP/1.1 {status_code} OK\r\n"
    response += "Content-Type: application/json\r\n"
    response += "Access-Control-Allow-Origin: *\r\n"
    response += "Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS\r\n"
    response += "Access-Control-Allow-Headers: Content-Type\r\n\r\n"
    response += data
    conn.send(response)

def handle_request(conn, path, method, query_params, body):
    if path in (
        "/generate_204",
        "/gen_204",
        "/library/test/success.html",
    ):
        send_response(conn, "", 204)
        return

    if path in ("/hotspot-detect.html", "/success.html"):
        conn.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n"
                  "<HTML><HEAD><TITLE>Success</TITLE></HEAD>"
                  "<BODY>Success</BODY></HTML>")
        return

    if path == "/system/info":
        info = {
            'unit_id': config.UNIT_ID,
            'model': config.UNIT_MODEL,
            'firmware': config.FW_VERSION,
            'free_heap': gc.mem_free(),
            'uptime': time.ticks_ms()
        }
        send_response(conn, info)

    elif path == "/actuators" and method == "GET":
        send_response(conn, device_manager.get_actuator_names())

    elif path == "/actuator" and method == "GET":
        name = query_params.get("name")
        if not name:
            send_response(conn, {"error": "Missing actuator name"}, 400)
            return
        result = device_manager.get_actuator_state(name)
        if result is None:
            send_response(conn, {"error": "Actuator not found"}, 404)
            return
        send_response(conn, result)

    elif path == "/actuator/control":
        name = query_params.get("name")
        method_param = query_params.get("method")
        if not name or not method_param:
            send_response(conn, {"error": "Missing parameters"}, 400)
            return
        params = query_params.copy()
        params.pop("name", None)
        params.pop("method", None)
        success = device_manager.invoke_actuator_method(name, method_param, params)
        send_response(conn, {"status": "OK"} if success else {"error": "Failed"}, 200 if success else 500)

    elif path == "/sensors" and method == "GET":
        send_response(conn, device_manager.get_sensor_names())

    elif path == "/sensor" and method == "GET":
        name = query_params.get("name")
        if not name:
            send_response(conn, {"error": "Missing sensor name"}, 400)
            return
        result = device_manager.get_sensor_reading(name)
        if result is None:
            send_response(conn, {"error": "Sensor not found"}, 404)
            return
        send_response(conn, result)

    elif path == "/automations" and method == "GET":
        send_response(conn, device_manager.get_automations_list())

    elif path == "/automation/toggle" and method == "POST":
        name = query_params.get("name") or (body.get("name") if body else None)
        if not name:
            send_response(conn, {"error": "Missing name"}, 400)
            return
        success = device_manager.toggle_automation(name)
        send_response(conn, {"status": "OK"} if success else {"error": "Not found"}, 200 if success else 404)

    elif path == "/automation/trigger" and method == "POST":
        event = query_params.get("event") or (body.get("event") if body else None)
        if not event:
            send_response(conn, {"error": "Missing event"}, 400)
            return
        device_manager.trigger_event(event)
        send_response(conn, {"status": "OK"})

    elif path == "/metadata" and method == "GET":
        send_response(conn, device_manager.get_metadata())

    elif method == "OPTIONS":
        send_response(conn, "")

def parse_request(request):
    try:
        lines = request.split("\r\n")
        method, full_path, _ = lines[0].split()
        if "?" in full_path:
            path, query_string = full_path.split("?", 1)
            query_params = dict(q.split("=") for q in query_string.split("&"))
        else:
            path = full_path
            query_params = {}
        body = None
        if method in ["POST", "PUT"]:
            body_data = lines[-1]
            try:
                body = json.loads(body_data)
            except:
                body = None
        return method, path, query_params, body
    except Exception as e:
        return None, None, {}, None

def start_server():
    address = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
    server = socket.socket()
    
    server.bind(address)
    server.listen(5)
        
    while True:
        try:
            conn, address = server.accept()
            request = conn.recv(1024).decode()
            method, path, query_params, body = parse_request(request)
            if method:
                handle_request(conn, path, method, query_params, body)
            conn.close()
        except Exception as e:
            print("Request handling error:", e)
        finally:
            gc.collect()

def start_dns_server(ap_ip='192.168.0.1'):
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind(('0.0.0.0', 53))
    
    while True:
        data, address = server.recvfrom(512)
        response = data[:2] + b'\x81\x80' + data[4:6] + data[4:6] + b'\x00\x00\x00\x00' + data[12:]

        response += b'\xc0\x0c\x00\x01\x00\x01\x00\x00\x00\x3c\x00\x04' + bytes(map(int, ap_ip.split('.')))
        server.sendto(response, address)

def main():
    unit_manager.load_config()

    if config.DEBUG:
        unit = unit_manager.get_config()
        
        print("\nChloroFill Unit")
        print(f"ID: {unit['id']}")
        print(f"Model: {unit['model']}")
        print(f"FW Version: {unit['fw_version']}")
        print(f"Name: {unit['name']}")

    setup_wifi()

    device_manager.load_devices()
    device_manager.load_automations("/configs/automations.json")
    
    device_manager.init_devices()
    device_manager.init_automations()

    import _thread
    _thread.start_new_thread(start_server, ())
    _thread.start_new_thread(start_dns_server, ())

    last_actuator_update = 0
    last_automation_update = 0

    while True:
        try:
            now = time.ticks_ms()

            if time.ticks_diff(now, last_actuator_update) >= config.UPDATE_INTERVAL:
                device_manager.update_actuators()
                last_actuator_update = now

            if time.ticks_diff(now, last_automation_update) >= config.AUTOMATION_INTERVAL:
                device_manager.update_automations()
                last_automation_update = now

            time.sleep_ms(10)

            if now % 10000 < 100:
                gc.collect()

        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(f'Loop error: {e}')
            import sys
            sys.print_exception(e)
            time.sleep_ms(1000)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        import sys
        sys.print_exception(e)
