import json

class UnitManager:
    def __init__(self, unit_id, unit_model, fw_version):
        self.config = {
            'id': unit_id,
            'model': unit_model,
            'fw_version': fw_version,
            'name': f"{unit_id}-{unit_model}"
        }
        self.config_file = '/unit_config.json'
    
    def load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                saved_config = json.load(f)
                self.config['name'] = saved_config.get('name', self.config['name'])
                print('Loaded unit configuration')
        except:
            self.save_config()
    
    def save_config(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump({'name': self.config['name']}, f)
        except Exception as e:
            print(f'Failed to save unit config: {e}')
    
    def set_unit_name(self, new_name):
        if not new_name:
            self.config['name'] = f"{self.config['id']}-{self.config['model']}"
        else:
            self.config['name'] = new_name
        self.save_config()
    
    def get_config(self):
        return self.config.copy()