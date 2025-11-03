from machine import Pin
import time

# Driver metadata
METADATA = {
    'methods': {
        'on': {
            'description': 'Turn pump on',
            'params': []
        },
        'off': {
            'description': 'Turn pump off',
            'params': []
        },
        'toggle': {
            'description': 'Toggle pump state',
            'params': []
        },
        'run_duration': {
            'description': 'Run pump for specific duration',
            'params': [
                {'name': 'duration', 'type': 'number', 'required': True}
            ]
        }
    },
    'exposed_states': ['state', 'run_time']
}

# State storage
states = {}

def _get_state(pin):
    """Get or create state for pin"""
    if pin not in states:
        states[pin] = {
            'active': False,
            'start_time': 0,
            'total_run_time': 0,
            'pin_obj': None
        }
    return states[pin]

def init(config):
    """Initialize pump"""
    pin = config['pins'][0]
    print(f"Pump Driver: Initializing pump on pin {pin}")
    
    state = _get_state(pin)
    state['pin_obj'] = Pin(pin, Pin.OUT)
    state['pin_obj'].value(0)
    state['active'] = False
    
    print(f"Pump Driver initialized for pin {pin}")

def on(config):
    """Turn pump on"""
    pin = config['pins'][0]
    state = _get_state(pin)
    
    if not state['active']:
        state['pin_obj'].value(1)
        state['active'] = True
        state['start_time'] = time.ticks_ms()
        print(f"Pump on pin {pin} turned ON")

def off(config):
    """Turn pump off"""
    pin = config['pins'][0]
    state = _get_state(pin)
    
    if state['active']:
        state['pin_obj'].value(0)
        state['active'] = False
        
        # Update total run time
        elapsed = time.ticks_diff(time.ticks_ms(), state['start_time'])
        state['total_run_time'] += elapsed
        
        print(f"Pump on pin {pin} turned OFF")

def toggle(config):
    """Toggle pump state"""
    pin = config['pins'][0]
    state = _get_state(pin)
    
    if state['active']:
        off(config)
    else:
        on(config)

def run_duration(config):
    """Run pump for specific duration"""
    pin = config['pins'][0]
    data = config.get('data', {})
    
    duration = int(data.get('duration', 1000))
    
    on(config)
    time.sleep_ms(duration)
    off(config)
    
    print(f"Pump on pin {pin} ran for {duration}ms")

def get_states(config):
    """Get pump states"""
    pin = config['pins'][0]
    state = _get_state(pin)
    
    current_run_time = 0
    if state['active']:
        current_run_time = time.ticks_diff(time.ticks_ms(), state['start_time'])
    
    return {
        'state': 'ON' if state['active'] else 'OFF',
        'run_time': state['total_run_time'] + current_run_time
    }

def update(config):
    """Update pump (no continuous update needed)"""
    pass