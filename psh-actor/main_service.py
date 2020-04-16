from constants import CONFIG_ROOMS
from constants import CONFIG_ROOM_NAME
from constants import CONFIG_ROOM_POINTS
from constants import CONFIG_CONNECTIVITY
from hub_communication_service import HubCommunicationService
from room import Room
from signal import pause

class MainService:

    def __init__(self):
        self.rooms = []
        self.communicationService = HubCommunicationService()

    def initialize(self, configuration):
        rooms = configuration.get(CONFIG_ROOMS)
        for room in rooms:
            room_obj = Room(room.get(CONFIG_ROOM_NAME))
            room_obj.initialize(room.get(CONFIG_ROOM_POINTS))
            self.rooms.append(room_obj)
        self.communicationService.initialize(configuration.get(CONFIG_CONNECTIVITY))

    def destroy(self):
        self.communicationService.destroy()

    def execute(self):
        pause()
