from constants import CONFIG_CONNECTIVITY
from constants import CONFIG_CONNECTIVITY_CLIENTNAME

import json

class ConfigurationService:

    DEFAULT_CONFIG_FILE = "./config/config.json"

    def __init__(self):
        pass

    def read_configuration(self):
        with open(self.DEFAULT_CONFIG_FILE) as f:
            config = json.load(f)
        return config

def print_actor_name():
    cs = ConfigurationService()
    configuration = cs.read_configuration()
    comm_config = configuration.get(CONFIG_CONNECTIVITY)
    client_name = comm_config.get(CONFIG_CONNECTIVITY_CLIENTNAME)
    print(client_name)

print_actor_name()