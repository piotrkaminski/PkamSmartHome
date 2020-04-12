from constants import CONFIG_ROOMS
from constants import CONFIG_ROOM_NAME
from constants import CONFIG_ROOM_POINTS
from room import Room
from signal import pause
import time

class MainService:

    def __init__(self):
        self.rooms = []

    def initialize(self, configuration):
        rooms = configuration.get(CONFIG_ROOMS)
        for room in rooms:
            room_obj = Room(room.get(CONFIG_ROOM_NAME))
            room_obj.initialize(room.get(CONFIG_ROOM_POINTS))
            self.rooms.append(room_obj)

    def execute(self):
        pause()
