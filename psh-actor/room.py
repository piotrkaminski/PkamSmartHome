from constants import CONFIG_ROOM_POINTS
from constants import CONFIG_POINT_TYPE
from constants import NAME_SEPARATOR
from point_factory import PointFactory

class Room:

    def __init__(self, name):
        self.name = NAME_SEPARATOR + name
        self.point_factory = PointFactory()
        self.points = []

    def initialize(self, configuration):
        for point in configuration:
            point_type = point.get(CONFIG_POINT_TYPE)
            point_obj = self.point_factory.createPoint(type=point_type, room_name=self.name, configuration=point)
            self.points.append(point_obj)