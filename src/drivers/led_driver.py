from machine import Pin
import time

# Driver metadata
METADATA = {
    'methods': {
        'on': {
            'description': 'Turn LED on',
            'params': []
        },
        'off': {
            'description': 'Turn LED off',
            'params': []
        },
        'toggle': {
            'description': 'Toggle LED state',
            'params': []
        },
        'blink': {
            'description': 'Blink LED',
            'params': [
                {'name': 'duration', 'type': 'number', 'required': False},
                {'name': 'interval', 'type': 'number', 'required': False}
            ]
        }
    },
    'exposed_states': ['state', 'blink_active', 'toggle_count']
}

# State storage
states = {}

def _get_state(pin):
    """Get or create state for pin"""
    if pin not in states:
        states[pin] = {
            'current_state': 0,
            'last_toggle': 0,
            'toggle_count': 0,
            'blink_active': False,
            'blink_start': 0,
            'blink_duration': 0,
            'blink_interval': 500,
            'pin_obj': None
        }
    return states[pin]

def init(config):
    """Initialize LED"""
    pin = config['pins'][0]
    print(f"LED Driver: Initializing LED on pin {pin}")
    
    state = _get_state(pin)
    state['pin_obj'] = Pin(pin, Pin.OUT)
    state['pin_obj'].value(0)
    state['current_state'] = 0
    
    print(f"LED Driver initialized for pin {pin}")

def on(config):
    """Turn LED on"""
    pin = config['pins'][0]
    state = _get_state(pin)
    
    state['pin_obj'].value(1)
    state['current_state'] = 1
    state['blink_active'] = False
    
    print(f"LED on pin {pin} turned ON")

def off(config):
    """Turn LED off"""
    pin = config['pins'][0]
    state = _get_state(pin)
    
    state['pin_obj'].value(0)
    state['current_state'] = 0
    state['blink_active'] = False
    
def toggle(config):
    """Toggle LED state"""
    pin = config['pins'][0]
    state = _get_state(pin)
    
    if state['current_state'] == 1:
        state['pin_obj'].value(0)
        state['current_state'] = 0
    else:
        state['pin_obj'].value(1)
        state['current_state'] = 1
    
    state['last_toggle'] = time.ticks_ms()
    state['toggle_count'] += 1
    state['blink_active'] = False

def blink(config):
    """Start blinking LED"""
    pin = config['pins'][0]
    state = _get_state(pin)
    data = config.get('data', {})
    
    duration = int(data.get('duration', 5000))
    interval = int(data.get('interval', 500))
    
    state['blink_active'] = True
    state['blink_start'] = time.ticks_ms()
    state['blink_duration'] = duration
    state['blink_interval'] = interval
    
    print(f"LED on pin {pin} starting blink for {duration}ms with {interval}ms interval")

def get_states(config):
    """Get LED states"""
    pin = config['pins'][0]
    state = _get_state(pin)
    
    return {
        'state': 'ON' if state['current_state'] == 1 else 'OFF',
        'blink_active': state['blink_active'],
        'toggle_count': state['toggle_count']
    }

def update(config):
    """Update LED (handle blinking)"""
    pin = config['pins'][0]
    state = _get_state(pin)
    now = time.ticks_ms()
    
    if state['blink_active']:
        if time.ticks_diff(now, state['blink_start']) > state['blink_duration']:
            state['blink_active'] = False
            state['pin_obj'].value(0)
            state['current_state'] = 0
            print(f"Blink completed for pin {pin}")
            return
        
        blink_cycle = time.ticks_diff(now, state['blink_start']) % (state['blink_interval'] * 2)
        should_be_on = blink_cycle < state['blink_interval']
        
        if should_be_on and state['current_state'] == 0:
            state['pin_obj'].value(1)
            state['current_state'] = 1
        elif not should_be_on and state['current_state'] == 1:
            state['pin_obj'].value(0)
            state['current_state'] = 0