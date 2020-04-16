from paho.mqtt.client import Client
from constants import CONFIG_CONNECTIVITY_CLIENTNAME
from constants import CONFIG_CONNECTIVITY_MQTTIP
from constants import CONFIG_CONNECTIVITY_MQTTPORT

class HubCommunicationService:

    def __init__(self):
        self.client = None

    def initialize(self, configuration):
        self.client = Client(configuration.get(CONFIG_CONNECTIVITY_CLIENTNAME))
        host = configuration.get(CONFIG_CONNECTIVITY_MQTTIP)
        port = configuration.get(CONFIG_CONNECTIVITY_MQTTPORT)
        self.client.connect(host=host, port=port)

    def sendStatusUpdate(self, channel, message):
        self.client.publish(topic=channel, payload=message)