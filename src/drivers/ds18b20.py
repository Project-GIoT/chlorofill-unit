from machine import Pin
import onewire
import ds18x20
import time

# Driver metadata
METADATA = {
    'readings': [
        {
            'name': 'temperature',
            'unit': '°C',
            'type': 'float',
            'description': 'Temperature in Celsius'
        },
        {
            'name': 'device_count',
            'unit': '',
            'type': 'int',
            'description': 'Number of connected sensors'
        }
    ]
}

# State storage
sensors = {}

def _get_sensor(pin):
    """Get or create sensor for pin"""
    if pin not in sensors:
        sensors[pin] = {
            'ds': None,
            'roms': [],
            'last_conversion': 0
        }
    return sensors[pin]

def init(config):
    """Initialize DS18B20 sensor"""
    pin = config['pins'][0]
    print(f"DS18B20 Driver: Initializing sensor on pin {pin}")
    
    sensor = _get_sensor(pin)
    
    try:
        ow = onewire.OneWire(Pin(pin))
        sensor['ds'] = ds18x20.DS18X20(ow)
        sensor['roms'] = sensor['ds'].scan()
        
        print(f"DS18B20: Found {len(sensor['roms'])} sensor(s) on pin {pin}")
        
        # Initial conversion
        if sensor['roms']:
            sensor['ds'].convert_temp()
            time.sleep_ms(750)
            sensor['last_conversion'] = time.ticks_ms()
            
    except Exception as e:
        print(f"DS18B20 initialization error on pin {pin}: {e}")
    
    print(f"DS18B20 Driver initialized for pin {pin}")

def read(config):
    """Read temperature from DS18B20"""
    pin = config['pins'][0]
    sensor = _get_sensor(pin)
    
    if not sensor['ds'] or not sensor['roms']:
        return {
            'temperature': -127.0,
            'device_count': 0,
            'status': 'no_sensor'
        }
    
    try:
        # Start conversion if enough time has passed
        now = time.ticks_ms()
        if time.ticks_diff(now, sensor['last_conversion']) > 1000:
            sensor['ds'].convert_temp()
            time.sleep_ms(750)
            sensor['last_conversion'] = now
        
        # Read temperature from first sensor
        temp = sensor['ds'].read_temp(sensor['roms'][0])
        
        return {
            'temperature': round(temp, 2),
            'device_count': len(sensor['roms']),
            'status': 'ok'
        }
        
    except Exception as e:
        print(f"DS18B20 read error on pin {pin}: {e}")
        return {
            'temperature': -127.0,
            'device_count': len(sensor['roms']),
            'status': 'error'
        }