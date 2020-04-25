from constants import CONFIG_ROOM_POINTS
from constants import CONFIG_POINT_TYPE
# from constants import NAME_SEPARATOR
from point_factory import PointFactory

class Room:

    def __init__(self, name):
        self.name = name
        self.point_factory = PointFactory()
        self.points = []

    def initialize(self, configuration, comm_service):
        for point in configuration:
            point_type = point.get(CONFIG_POINT_TYPE)
            point_obj = self.point_factory.createPoint(
                type=point_type, 
                room_name=self.name, 
                configuration=point, 
                comm_service=comm_service)
            self.points.append(point_obj)

    def updateStatus(self, point_id, message):
        for point in self.points:
            if point.id == point_id:
                point.updateStatus(point_id, message)