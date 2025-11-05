from machine import Pin, ADC
import time

METADATA = {
    'readings': [
        {
            'name': 'reading',
            'unit': '',
            'type': 'int',
            'description': 'ADC (0-1023)'
        },
        {
            'name': 'percent',
            'unit': '%',
            'type': 'float',
            'description': 'ADC in Percent'
        },
        {
            'name': 'status',
            'unit': '',
            'type': 'string',
            'description': 'Moisture status (Dry/Moist/Wet)'
        }
    ]
}

sensors = {}

DRY_VALUE = 3000
WET_VALUE = 1000

def _get_sensor(pin):
    if pin not in sensors:
        sensors[pin] = {
            'adc': None,
            'readings': []
        }
    return sensors[pin]

def init(config):
    pin = config['pins'][0]
    print(f"Soil Moisture Driver: Initializing sensor on pin {pin}")
    
    sensor = _get_sensor(pin)
    
    try:
        sensor['adc'] = ADC(Pin(pin))
        sensor['adc'].atten(ADC.ATTN_11DB)
        sensor['adc'].width(ADC.WIDTH_12BIT)
        print(f"Soil Moisture Driver initialized for pin {pin}")
    except Exception as e:
        print(f"Soil Moisture initialization error on pin {pin}: {e}")

def read(config):
    pin = config['pins'][0]
    sensor = _get_sensor(pin)
    
    if not sensor['adc']:
        return {
            'reading': 0,
            'percent': 0.0,
            'status': 'error'
        }
    
    try:
        samples = []
        for _ in range(5):
            samples.append(sensor['adc'].read())
            time.sleep_ms(10)
        
        raw_value = sum(samples) // len(samples)
        
        scaled_value = int((raw_value / 4095) * 1023)
        
        if raw_value >= DRY_VALUE:
            moisture_percent = 0.0
        elif raw_value <= WET_VALUE:
            moisture_percent = 100.0
        else:
            moisture_percent = 100.0 - ((raw_value - WET_VALUE) / (DRY_VALUE - WET_VALUE) * 100.0)
        
        if moisture_percent < 30:
            status = 'dry'
        elif moisture_percent < 70:
            status = 'moist'
        else:
            status = 'wet'
        
        return {
            'reading': scaled_value,
            'percent': round(moisture_percent, 1),
            'status': status
        }
        
    except Exception as e:
        return {
            'reading': 0,
            'percent': 0.0,
            'status': 'error'
        }