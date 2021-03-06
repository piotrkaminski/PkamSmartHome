from constants import CONFIG_ROOMS
from constants import CONFIG_ROOM_NAME
from constants import CONFIG_ROOM_POINTS
from constants import CONFIG_CONNECTIVITY
from constants import NAME_SEPARATOR
from hub_communication_service import HubCommunicationService
from room import Room
import logging

class RoomsService:

    def __init__(self):
        self.rooms = []

    def initialize(self, configuration, comm_service):
        if configuration is None or configuration.get(CONFIG_ROOMS) is None:
            logging.warning("Configuration error, no {} definition".format(CONFIG_ROOMS))
            return
        rooms = configuration.get(CONFIG_ROOMS)
        for room in rooms:
            room_obj = Room(room.get(CONFIG_ROOM_NAME))
            room_obj.initialize(configuration=room.get(CONFIG_ROOM_POINTS), comm_service=comm_service)
            self.rooms.append(room_obj)

    def get_room_name(self, point_id):
        if point_id is None:
            return None
        idx = point_id[1:len(point_id)].find(NAME_SEPARATOR)
        if idx < 0:
            return None
        return point_id[1: idx+1]
            
    def updateStatus(self, point_id, message):
        room_name = self.get_room_name(point_id)
        if room_name is None:
            logging.info("Room name not found in {0}, status update skipped".format(point_id))
        for room in self.rooms:
            if room.name == room_name:
                room.updateStatus(point_id, message)

    def reset(self):
        for room in self.rooms:
            room.reset()

    def notify_current_state(self):
        for room in self.rooms:
            room.notify_current_state()