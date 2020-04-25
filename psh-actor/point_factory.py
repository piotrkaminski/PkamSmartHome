from constants import CONFIG_POINT_NAME
from constants import CONFIG_POINT_TYPE
from constants import CONFIG_POINT_TYPE_LIGHT
from constants import CONFIG_POINT_CONTROLPIN
from constants import CONFIG_POINT_BUTTONPIN
from constants import NAME_SEPARATOR
from light_point import LightPoint

class PointFactory:

    def __init__(self):
        pass

    def createPoint(self, type, room_name, configuration, comm_service):
        point_type = configuration.get(CONFIG_POINT_TYPE)
        if point_type == CONFIG_POINT_TYPE_LIGHT:
            return LightPoint(id=NAME_SEPARATOR + room_name + NAME_SEPARATOR + configuration.get(CONFIG_POINT_NAME),
                controlPin=configuration.get(CONFIG_POINT_CONTROLPIN),
                buttonPin=configuration.get(CONFIG_POINT_BUTTONPIN),
                comm_service=comm_service)
        else:
            raise Exception("Unrecognized point type: {type}".format(type=point_type))