from constants import CONFIG_CONNECTIVITY_CLIENTNAME
from constants import CONFIG_CONNECTIVITY_MQTTIP
from constants import CONFIG_CONNECTIVITY_MQTTPORT
from constants import NAME_SEPARATOR
from paho.mqtt.client import Client
from signal import pause


class HubCommunicationService:

    def __init__(self):
        self.client = None
        self.client_name = None

    def initialize(self, configuration):
        self.client_name = configuration.get(CONFIG_CONNECTIVITY_CLIENTNAME)
        self.client = Client(self.client_name)
        host = configuration.get(CONFIG_CONNECTIVITY_MQTTIP)
        port = configuration.get(CONFIG_CONNECTIVITY_MQTTPORT)
        self.client.enable_logger()
        self.client.on_message = self.on_message
        self.client.on_connect = self.on_connect
        self.client.connect(host=host, port=port)
        self.client.loop_start()

    def destroy(self): 
        self.client.loop_stop()
        self.client.disconnect()
        
    def create_topic_name(self):
        # topic format /Actor/In/#
        return "{sep}{name}{sep}In{sep}#".format(sep=NAME_SEPARATOR, name=self.client_name)

    def on_message(self, client, userdata, message):
        topic = message.topic
        payload = str(message.payload.decode("utf-8"))
        print("Msg rcv: {0} msg: {1}".format(topic, payload))
        self.process_message(channel=topic, message=payload)

    def on_connect(self, client, userdata, flags, rc):
        print("Connection returned result: " + str(rc))
        topic = "/Pi1/In/#"
        #topic = self.create_topic_name()
        print("Subscribing to topic {}".format(topic))
        self.client.subscribe(topic)

    def sendStatusUpdate(self, channel, message):
        self.client.publish(topic=channel, payload=message)

    def process_message(self, channel, message):
        print("Msg prc: {0} msg: {1}".format(channel, message))



main = HubCommunicationService()
main.initialize({
        "ClientName": "Pi1",
        "MqttIp": "localhost",
        "MqttPort": 1883
    })
pause()