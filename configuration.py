import json

class ConfigurationService:

    DEFAULT_CONFIG_FILE = "./config/config.json"

    def __init__(self):
        pass

    def read_configuration(self):
        with open(self.DEFAULT_CONFIG_FILE) as f:
            config = json.load(f)
        return config
