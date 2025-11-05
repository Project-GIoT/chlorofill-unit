from machine import Pin, time_pulse_us
import time

METADATA = {
    'readings': [
        {
            'name': 'volume_liters',
            'unit': 'L',
            'type': 'float',
            'description': 'Water volume in liters'
        },
        {
            'name': 'percent_full',
            'unit': '%',
            'type': 'float',
            'description': 'Percentage of tank capacity'
        }
    ]
}

sensors = {}

TANK_HEIGHT_CM = 30.0       # Height from sensor to bottom
TANK_AREA_CM2 = 500.0       # Cross-sectional area of tank
TANK_CAPACITY_L = 15.0      # Maximum capacity in liters

def _get_sensor(pins):
    key = f"{pins[0]}_{pins[1]}"
    if key not in sensors:
        sensors[key] = {
            'trigger': None,
            'echo': None,
            'readings': []
        }
    return sensors[key]

def init(config):
    trigger_pin = config['pins'][0]
    echo_pin = config['pins'][1]
    print(f"Water Volume Driver: Initializing sensor on pins {trigger_pin} (trigger), {echo_pin} (echo)")
    
    sensor = _get_sensor(config['pins'])
    
    try:
        sensor['trigger'] = Pin(trigger_pin, Pin.OUT)
        sensor['echo'] = Pin(echo_pin, Pin.IN)
        sensor['trigger'].value(0)
        time.sleep_ms(100)
        print(f"Water Volume Driver initialized")
    except Exception as e:
        print(f"Water Volume initialization error: {e}")

def _measure_distance(trigger, echo):
    try:
        trigger.value(0)
        time.sleep_us(2)
        trigger.value(1)
        time.sleep_us(10)
        trigger.value(0)
        
        duration = time_pulse_us(echo, 1, 30000)
        
        if duration < 0:
            return None
        
        # Calculate distance in cm (speed of sound = 343 m/s)
        distance = (duration * 0.0343) / 2
        
        return distance
        
    except Exception as e:
        return None

def read(config):
    sensor = _get_sensor(config['pins'])
    
    if not sensor['trigger'] or not sensor['echo']:
        return {
            'volume_liters': 0.0,
            'percent_full': 0.0,
            'status': 'error'
        }
    
    try:
        distances = []
        for _ in range(3):
            dist = _measure_distance(sensor['trigger'], sensor['echo'])
            if dist is not None and 2.0 <= dist <= 400.0:  # Valid range
                distances.append(dist)
            time.sleep_ms(100)
        
        if not distances:
            return {
                'volume_liters': 0.0,
                'percent_full': 0.0,
                'status': 'no_reading'
            }
        
        distance_cm = sum(distances) / len(distances)
        water_level_cm = max(0, TANK_HEIGHT_CM - distance_cm)
        volume_liters = (water_level_cm * TANK_AREA_CM2) / 1000.0
        percent_full = min(100.0, (volume_liters / TANK_CAPACITY_L) * 100.0)
        
        return {
            'volume_liters': round(volume_liters, 2),
            'percent_full': round(percent_full, 1),
            'status': 'ok'
        }
        
    except Exception as e:
        return {
            'volume_liters': 0.0,
            'percent_full': 0.0,
            'status': 'error'
        }