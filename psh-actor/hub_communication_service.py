from constants import CONFIG_CONNECTIVITY
from constants import CONFIG_CONNECTIVITY_CLIENTNAME
from constants import CONFIG_CONNECTIVITY_MQTTIP
from constants import CONFIG_CONNECTIVITY_MQTTPORT
from constants import NAME_SEPARATOR
from constants import TOPIC_IN
from constants import TOPIC_OUT
from constants import TOPIC_ADMIN
from constants import COMMAND_RESET
from constants import COMMAND_NOTIFY_CURRENT_STATE
from signal import pause
import logging
import paho.mqtt.client as mqtt

class HubCommunicationService:

    def __init__(self):
        self.client = None        
        self.client_name = None
        self.rooms_service = None

    def initialize(self, configuration, rooms_service):
        self.rooms_service = rooms_service
        comm_config = configuration.get(CONFIG_CONNECTIVITY)
        self.client_name = comm_config.get(CONFIG_CONNECTIVITY_CLIENTNAME)
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, self.client_name)
        host = comm_config.get(CONFIG_CONNECTIVITY_MQTTIP)
        port = comm_config.get(CONFIG_CONNECTIVITY_MQTTPORT)
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
        return "{sep}{name}{sep}{tin}{sep}#".format(sep=NAME_SEPARATOR, tin = TOPIC_IN, name=self.client_name)

    def get_point_id(self, channel):
        if channel is None:
            return None
        topic_indicator = NAME_SEPARATOR + TOPIC_IN + NAME_SEPARATOR
        idx = channel.find(topic_indicator)
        if idx < 0:
            return None
        return channel[idx+len(topic_indicator)-1:len(channel)]

    def is_admin_channel(self, channel):
        if channel is None:
            return False
        admin_indicator = NAME_SEPARATOR + TOPIC_ADMIN
        idx = channel.find(admin_indicator)
        if idx < 0:
            return False
        return True
        

    def get_channel(self, point_id):
        # topic format /Actor/Out/PointId
        return "{sep}{act}{sep}{tout}{id}".format(
            sep=NAME_SEPARATOR, 
            tout=TOPIC_OUT, 
            act=self.client_name,
            id=point_id)


    def on_message(self, client, userdata, message):
        topic = message.topic
        payload = str(message.payload.decode("utf-8"))
        logging.debug("Msg rcv: {0} msg: {1}".format(topic, payload))
        self.process_message(channel=topic, message=payload)

    def on_connect(self, client, userdata, flags, reason_code, properties ):
        logging.info("Connected to mqtt service on {0}:{1} ".format(client._host, client._port))
        topic = self.create_topic_name()
        logging.info("Subscribing to topic {}".format(topic))
        self.client.subscribe(topic)

    def sendStatusUpdate(self, point_id, message):
        topic = self.get_channel(point_id)
        self.client.publish(topic=topic, payload=message)
        logging.debug("Msg snd: {0} msg: {1}".format(topic, message))

    def process_message(self, channel, message):
        if self.is_admin_channel(channel):
            self.process_admin_message(channel, message)
            return

        point_id = self.get_point_id(channel)
        if point_id is None:
            logging.info("Point_id not determined for channel {0} and message {1}, skipped"
                .format(channel, message))
        else:
            self.rooms_service.updateStatus(point_id=point_id, message=message)
            
    def process_admin_message(self, channel, message):
        logging.info("Admin message received: channel {0} message {1}"
                .format(channel, message))
        if message == COMMAND_RESET:
            self.rooms_service.reset()
        if message == COMMAND_NOTIFY_CURRENT_STATE:
            self.rooms_service.notify_current_state()
