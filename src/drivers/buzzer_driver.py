from machine import Pin, PWM
import time

# Driver metadata
METADATA = {
    'methods': {
        'on': {
            'description': 'Turn buzzer on',
            'params': [
                {'name': 'frequency', 'type': 'number', 'required': False}
            ]
        },
        'off': {
            'description': 'Turn buzzer off',
            'params': []
        },
        'beep': {
            'description': 'Single beep',
            'params': [
                {'name': 'duration', 'type': 'number', 'required': False},
                {'name': 'frequency', 'type': 'number', 'required': False}
            ]
        },
        'tone': {
            'description': 'Play specific tone',
            'params': [
                {'name': 'frequency', 'type': 'number', 'required': True}
            ]
        }
    },
    'exposed_states': ['state', 'frequency']
}

# State storage
states = {}

def _get_state(pin):
    """Get or create state for pin"""
    if pin not in states:
        states[pin] = {
            'active': False,
            'frequency': 2000,
            'pwm_obj': None
        }
    return states[pin]

def init(config):
    """Initialize buzzer"""
    pin = config['pins'][0]
    print(f"Buzzer Driver: Initializing buzzer on pin {pin}")
    
    state = _get_state(pin)
    state['pwm_obj'] = PWM(Pin(pin), freq=2000, duty=0)
    state['active'] = False
    
    print(f"Buzzer Driver initialized for pin {pin}")

def on(config):
    """Turn buzzer on"""
    pin = config['pins'][0]
    state = _get_state(pin)
    data = config.get('data', {})
    
    frequency = int(data.get('frequency', 2000))
    
    state['pwm_obj'].freq(frequency)
    state['pwm_obj'].duty(512)  # 50% duty cycle
    state['active'] = True
    state['frequency'] = frequency
    
    print(f"Buzzer on pin {pin} turned ON at {frequency}Hz")

def off(config):
    """Turn buzzer off"""
    pin = config['pins'][0]
    state = _get_state(pin)
    
    state['pwm_obj'].duty(0)
    state['active'] = False
    
    print(f"Buzzer on pin {pin} turned OFF")

def beep(config):
    """Single beep"""
    pin = config['pins'][0]
    data = config.get('data', {})
    
    duration = int(data.get('duration', 200))
    frequency = int(data.get('frequency', 2000))
    
    # Temporarily turn on
    config_on = {'pins': [pin], 'data': {'frequency': frequency}}
    on(config_on)
    
    time.sleep_ms(duration)
    
    # Turn off
    off(config)
    
    print(f"Buzzer on pin {pin} beeped for {duration}ms")

def tone(config):
    """Play specific tone"""
    pin = config['pins'][0]
    data = config.get('data', {})
    
    frequency = int(data.get('frequency', 2000))
    
    config_on = {'pins': [pin], 'data': {'frequency': frequency}}
    on(config_on)

def get_states(config):
    """Get buzzer states"""
    pin = config['pins'][0]
    state = _get_state(pin)
    
    return {
        'state': 'ON' if state['active'] else 'OFF',
        'frequency': state['frequency']
    }

def update(config):
    """Update buzzer (no continuous update needed)"""
    pass