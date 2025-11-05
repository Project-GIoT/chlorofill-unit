import json
import time
from machine import Pin

class DeviceManager:
    def __init__(self):
        self.actuators = []
        self.sensors = []
        self.automations = []
        self.drivers = {}
        self.events = {}
        self.loaded_drivers = set()
        
    def load_devices(self):
        self.load_actuators('/configs/actuators.json')
        self.load_sensors('/configs/sensors.json')
        
        for actuator in self.actuators:
            self._load_driver(actuator['driver'])
        
        for sensor in self.sensors:
            self._load_driver(sensor['driver'])
    
    def load_actuators(self, path):
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                self.actuators = data
                print(f'Loaded {len(self.actuators)} actuators')
        except Exception as e:
            print(f'Failed to load actuators: {e}')
    
    def load_sensors(self, path):
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                self.sensors = data
                print(f'Loaded {len(self.sensors)} sensors')
        except Exception as e:
            print(f'Failed to load sensors: {e}')
    
    def load_automations(self, path):
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                for automation in data:
                    automation['last_trigger_time'] = 0
                    automation['enabled'] = automation.get('enabled', True)
                    automation['cooldown_ms'] = automation.get('cooldown_ms', 1000)
                self.automations = data
                print(f'Loaded {len(self.automations)} automations')
        except Exception as e:
            print(f'Failed to load automations: {e}')
    
    def _load_driver(self, driver_name):
        if driver_name in self.loaded_drivers:
            return True
        
        try:
            import sys
            
            if '/drivers' not in sys.path:
                sys.path.append('/drivers')
            
            module = __import__(driver_name)
            
            self.drivers[driver_name] = module
            self.loaded_drivers.add(driver_name)
            print(f'Loaded driver: {driver_name}')
            return True
        except Exception as e:
            print(f'Failed to load driver {driver_name}: {e}')
            import sys
            sys.print_exception(e)
            return False
    
    def init_devices(self):
        for actuator in self.actuators:
            self._init_actuator(actuator)
        
        for sensor in self.sensors:
            self._init_sensor(sensor)
    
    def _init_actuator(self, actuator):
        try:
            driver = self.drivers.get(actuator['driver'])
            if driver and hasattr(driver, 'init'):
                config = {
                    'id': actuator['id'],
                    'pins': actuator['pins']
                }
                driver.init(config)
                print(f"Initialized actuator: {actuator['id']}")
        except Exception as e:
            print(f"Failed to initialize actuator {actuator['id']}: {e}")
    
    def _init_sensor(self, sensor):
        try:
            driver = self.drivers.get(sensor['driver'])
            if driver and hasattr(driver, 'init'):
                config = {
                    'id': sensor['id'],
                    'pins': sensor['pins']
                }
                driver.init(config)
                print(f"Initialized sensor: {sensor['id']}")
        except Exception as e:
            print(f"Failed to initialize sensor {sensor['id']}: {e}")
    
    def init_automations(self):
        for automation in self.automations:
            condition = automation.get('condition', {})
            if condition.get('type') == 'Physical':
                pin = condition.get('pin', -1)
                if pin >= 0:
                    Pin(pin, Pin.IN, Pin.PULL_UP)
                    print(f"Initialized physical pin {pin} for automation {automation['id']}")
    
    def update_actuators(self):
        for actuator in self.actuators:
            try:
                driver = self.drivers.get(actuator['driver'])
                if driver and hasattr(driver, 'update'):
                    config = {
                        'id': actuator['id'],
                        'pins': actuator['pins']
                    }
                    driver.update(config)
            except Exception as e:
                pass  # Silent update errors
    
    def update_automations(self):
        current_time = time.ticks_ms()
        
        for automation in self.automations:
            if not automation.get('enabled', True):
                continue
            
            should_trigger = False
            condition = automation.get('condition', {})
            condition_type = condition.get('type')
            
            if condition_type == 'State':
                should_trigger = self._check_state_condition(automation)
            elif condition_type == 'Signal':
                should_trigger = self._check_signal_condition(automation)
            elif condition_type == 'Physical':
                should_trigger = self._check_physical_condition(automation)
            elif condition_type == 'Schedule':
                should_trigger = self._check_schedule_condition(automation, current_time)
            
            cooldown = automation.get('cooldown_ms', 1000)
            if should_trigger and time.ticks_diff(current_time, automation['last_trigger_time']) > cooldown:
                # print(f"Triggering automation: {automation['id']}")
                self._execute_automation_actions(automation)
                automation['last_trigger_time'] = current_time
    
    def _check_state_condition(self, automation):
        condition = automation.get('condition', {})
        sensor_name = condition.get('sensor')
        field = condition.get('field')
        operator = condition.get('operator')
        threshold = condition.get('threshold', 0)
        
        reading = self.get_sensor_reading(sensor_name)
        if not reading or field not in reading:
            return False
        
        value = reading[field]
        
        if operator == '>':
            return value > threshold
        elif operator == '<':
            return value < threshold
        elif operator == '>=':
            return value >= threshold
        elif operator == '<=':
            return value <= threshold
        elif operator == '==':
            return abs(value - threshold) < 0.001
        
        return False
    
    def _check_signal_condition(self, automation):
        condition = automation.get('condition', {})
        signal_name = condition.get('signal')
        
        if signal_name in self.events and self.events[signal_name]:
            self.events[signal_name] = False
            return True
        return False
    
    def _check_physical_condition(self, automation):
        condition = automation.get('condition', {})
        pin_num = condition.get('pin', -1)
        trigger_high = condition.get('trigger_high', True)
        
        if pin_num < 0:
            return False
        
        pin = Pin(pin_num, Pin.IN, Pin.PULL_UP)
        pin_state = pin.value()
        
        return (pin_state == 1) if trigger_high else (pin_state == 0)
    
    def _check_schedule_condition(self, automation, current_time):
        condition = automation.get('condition', {})
        start_time = condition.get('start_time', 0)
        end_time = condition.get('end_time', 86400)
        
        seconds_in_day = (current_time // 1000) % 86400
        return start_time <= seconds_in_day <= end_time
    
    def _execute_automation_actions(self, automation):
        actions = automation.get('actions', [])
        
        for action in actions:
            action_type = action.get('type')
            
            if action_type == 'Control':
                device_name = action.get('device')
                method = action.get('method')
                params_str = action.get('params', '')
                
                params = {}
                if params_str:
                    for pair in params_str.split('&'):
                        if '=' in pair:
                            key, value = pair.split('=', 1)
                            params[key] = value
                
                self.invoke_actuator_method(device_name, method, params)
                
            elif action_type == 'Signal':
                signal_name = action.get('signal')
                self.trigger_event(signal_name)
                
            elif action_type == 'Delay':
                delay_ms = action.get('delay_ms', 1000)
                time.sleep_ms(delay_ms)
    
    def get_actuator_ids(self):
        return [a['id'] for a in self.actuators]
    
    def get_sensor_ids(self):
        return [s['id'] for s in self.sensors]
    
    def get_actuator_state(self, id):
        actuator = self._find_actuator(id)
        if not actuator:
            return None
        
        driver = self.drivers.get(actuator['driver'])
        if not driver or not hasattr(driver, 'get_states'):
            return None
        
        try:
            config = {
                'id': actuator['id'],
                'pins': actuator['pins']
            }
            return driver.get_states(config)
        except Exception as e:
            print(f'Error getting actuator state: {e}')
            return None
    
    def get_sensor_reading(self, id):
        sensor = self._find_sensor(id)
        if not sensor:
            return None
        
        driver = self.drivers.get(sensor['driver'])
        if not driver or not hasattr(driver, 'read'):
            return None
        
        try:
            config = {
                'id': sensor['id'],
                'pins': sensor['pins']
            }
            return driver.read(config)
        except Exception as e:
            print(f'Error reading sensor: {e}')
            return None
    
    def invoke_actuator_method(self, id, method, params=None):
        actuator = self._find_actuator(id)
        if not actuator:
            return False
        
        driver = self.drivers.get(actuator['driver'])
        if not driver or not hasattr(driver, method):
            return False
        
        try:
            config = {
                'id': actuator['id'],
                'pins': actuator['pins'],
                'data': params or {}
            }
            method_func = getattr(driver, method)
            method_func(config)
            return True
        except Exception as e:
            print(f'Error invoking method {method}: {e}')
            return False
    
    def _find_actuator(self, id):
        for actuator in self.actuators:
            if actuator['id'] == id:
                return actuator
        return None
    
    def _find_sensor(self, id):
        for sensor in self.sensors:
            if sensor['id'] == id:
                return sensor
        return None
    
    def trigger_event(self, event_name):
        self.events[event_name] = True
        print(f'Event triggered: {event_name}')
    
    def get_automations_list(self):
        result = []
        for automation in self.automations:
            result.append({
                'name': automation['name'],
                'id': automation['id'],
                'description': automation.get('description', ''),
                'enabled': automation.get('enabled', True),
                'condition_type': automation.get('condition', {}).get('type')
            })
        return result
    
    def toggle_automation(self, id):
        for automation in self.automations:
            if automation['id'] == id:
                automation['enabled'] = not automation.get('enabled', True)
                print(f"Automation {id} {'enabled' if automation['enabled'] else 'disabled'}")
                return True
        return False
    
    def get_devices(self):
        metadata = {
            'actuators': [],
            'sensors': []
        }
        
        for actuator in self.actuators:
            driver = self.drivers.get(actuator['driver'])
            meta = {
                'name': actuator['name'],
                'id': actuator['id'],
                'driver': actuator['driver'],
                'type': 'actuator'
            }
            
            if driver and hasattr(driver, 'METADATA'):
                meta.update(driver.METADATA)
            
            metadata['actuators'].append(meta)
        
        for sensor in self.sensors:
            driver = self.drivers.get(sensor['driver'])
            meta = {
                'name': sensor['name'],
                'id': sensor['id'],
                'driver': sensor['driver'],
                'type': 'sensor'
            }
            
            if driver and hasattr(driver, 'METADATA'):
                meta.update(driver.METADATA)
            
            metadata['sensors'].append(meta)
        
        return metadata