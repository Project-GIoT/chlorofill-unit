from machine import Pin, PWM
import time

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

states = {}

def _get_state(pin):
    if pin not in states:
        states[pin] = {
            'active': False,
            'frequency': 2000,
            'pwm_obj': None
        }
    return states[pin]

def init(config):
    pin = config['pins'][0]
    print(f"Buzzer Driver: Initializing buzzer on pin {pin}")
    
    state = _get_state(pin)
    state['pwm_obj'] = PWM(Pin(pin), freq=2000, duty_u16=0)
    state['active'] = False
    
    print(f"Buzzer Driver initialized for pin {pin}")

def on(config):
    pin = config['pins'][0]
    state = _get_state(pin)
    data = config.get('data', {})
    
    frequency = int(data.get('frequency', 2000))
    
    state['pwm_obj'].freq(frequency)
    state['pwm_obj'].duty(512)  # 50% duty cycle
    state['active'] = True
    state['frequency'] = frequency
    
def off(config):
    pin = config['pins'][0]
    state = _get_state(pin)
    
    state['pwm_obj'].duty(0)
    state['active'] = False

def beep(config):
    pin = config['pins'][0]
    data = config.get('data', {})
    
    duration = int(data.get('duration', 200))
    frequency = int(data.get('frequency', 2000))
    
    config_on = {'pins': [pin], 'data': {'frequency': frequency}}
    on(config_on)
    
    time.sleep_ms(duration)
    
    off(config)

def tone(config):
    pin = config['pins'][0]
    data = config.get('data', {})
    
    frequency = int(data.get('frequency', 2000))
    
    config_on = {'pins': [pin], 'data': {'frequency': frequency}}
    on(config_on)

def get_states(config):
    pin = config['pins'][0]
    state = _get_state(pin)
    
    return {
        'state': 'ON' if state['active'] else 'OFF',
        'frequency': state['frequency']
    }

def update(config):
    pass