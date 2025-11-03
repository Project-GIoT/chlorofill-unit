from machine import Pin, ADC
import time

# Driver metadata
METADATA = {
    'readings': [
        {
            'name': 'raw_value',
            'unit': '',
            'type': 'int',
            'description': 'Raw ADC value'
        },
        {
            'name': 'scaled_value',
            'unit': '',
            'type': 'int',
            'description': 'Scaled value (0-1023)'
        },
        {
            'name': 'moisture_percent',
            'unit': '%',
            'type': 'float',
            'description': 'Moisture percentage'
        },
        {
            'name': 'status',
            'unit': '',
            'type': 'string',
            'description': 'Moisture status (dry/moist/wet)'
        }
    ]
}

# State storage
sensors = {}

# Calibration values (adjust based on your sensor)
DRY_VALUE = 3000      # Value when sensor is in air
WET_VALUE = 1000      # Value when sensor is in water

def _get_sensor(pin):
    """Get or create sensor for pin"""
    if pin not in sensors:
        sensors[pin] = {
            'adc': None,
            'readings': []
        }
    return sensors[pin]

def init(config):
    """Initialize soil moisture sensor"""
    pin = config['pins'][0]
    print(f"Soil Moisture Driver: Initializing sensor on pin {pin}")
    
    sensor = _get_sensor(pin)
    
    try:
        sensor['adc'] = ADC(Pin(pin))
        sensor['adc'].atten(ADC.ATTN_11DB)  # Full range: 0-3.3V
        sensor['adc'].width(ADC.WIDTH_12BIT)  # 0-4095
        print(f"Soil Moisture Driver initialized for pin {pin}")
    except Exception as e:
        print(f"Soil Moisture initialization error on pin {pin}: {e}")

def read(config):
    """Read soil moisture sensor"""
    pin = config['pins'][0]
    sensor = _get_sensor(pin)
    
    if not sensor['adc']:
        return {
            'raw_value': 0,
            'scaled_value': 0,
            'moisture_percent': 0.0,
            'status': 'error'
        }
    
    try:
        # Read multiple samples and average
        samples = []
        for _ in range(5):
            samples.append(sensor['adc'].read())
            time.sleep_ms(10)
        
        raw_value = sum(samples) // len(samples)
        
        # Scale to 0-1023 range (like Arduino)
        scaled_value = int((raw_value / 4095) * 1023)
        
        # Calculate moisture percentage (inverted: higher ADC = drier)
        if raw_value >= DRY_VALUE:
            moisture_percent = 0.0
        elif raw_value <= WET_VALUE:
            moisture_percent = 100.0
        else:
            moisture_percent = 100.0 - ((raw_value - WET_VALUE) / (DRY_VALUE - WET_VALUE) * 100.0)
        
        # Determine status
        if moisture_percent < 30:
            status = 'dry'
        elif moisture_percent < 70:
            status = 'moist'
        else:
            status = 'wet'
        
        return {
            'raw_value': raw_value,
            'scaled_value': scaled_value,
            'moisture_percent': round(moisture_percent, 1),
            'status': status
        }
        
    except Exception as e:
        print(f"Soil Moisture read error on pin {pin}: {e}")
        return {
            'raw_value': 0,
            'scaled_value': 0,
            'moisture_percent': 0.0,
            'status': 'error'
        }