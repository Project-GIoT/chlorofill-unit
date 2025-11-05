from machine import Pin
import onewire
import ds18x20
import time

METADATA = {
    'readings': [
        {
            'name': 'temperature',
            'unit': '°C',
            'type': 'float',
            'description': 'Temperature in Celsius'
        }
    ]
}

sensors = {}

def _get_sensor(pin):
    if pin not in sensors:
        sensors[pin] = {
            'ds': None,
            'roms': [],
            'last_conversion': 0
        }
    return sensors[pin]

def init(config):
    pin = config['pins'][0]
    print(f"DS18B20 Driver: Initializing sensor on pin {pin}")
    
    sensor = _get_sensor(pin)
    
    try:
        ow = onewire.OneWire(Pin(pin))
        sensor['ds'] = ds18x20.DS18X20(ow)
        sensor['roms'] = sensor['ds'].scan()
        
        print(f"DS18B20: Found {len(sensor['roms'])} sensor(s) on pin {pin}")
        
        if sensor['roms']:
            sensor['ds'].convert_temp()
            time.sleep_ms(750)
            sensor['last_conversion'] = time.ticks_ms()
            
    except Exception as e:
        print(f"DS18B20 initialization error on pin {pin}: {e}")
    
    print(f"DS18B20 Driver initialized for pin {pin}")

def read(config):
    pin = config['pins'][0]
    sensor = _get_sensor(pin)
    
    if not sensor['ds'] or not sensor['roms']:
        return {
            'temperature': -127.0,
            'status': 'no_sensor'
        }
    
    try:
        now = time.ticks_ms()
        if time.ticks_diff(now, sensor['last_conversion']) > 1000:
            sensor['ds'].convert_temp()
            time.sleep_ms(750)
            sensor['last_conversion'] = now
        
        temp = sensor['ds'].read_temp(sensor['roms'][0])
        
        return {
            'temperature': round(temp, 2),
            'status': 'ok'
        }
        
    except Exception as e:
        return {
            'temperature': -127.0,
            'status': 'error'
        }