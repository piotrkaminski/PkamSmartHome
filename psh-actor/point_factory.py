from constants import CONFIG_POINT_NAME
from constants import CONFIG_POINT_TYPE
from constants import CONFIG_POINT_TYPE_LIGHT
from constants import CONFIG_POINT_TYPE_BLIND
from constants import CONFIG_POINT_CONTROLPIN
from constants import CONFIG_POINT_BUTTONPIN
from constants import NAME_SEPARATOR
from light_point import LightPoint
from blind_point import BlindPoint

class PointFactory:

    def __init__(self):
        pass

    def createPoint(self, room_name, configuration, comm_service):
        point_name = configuration.get(CONFIG_POINT_NAME)
        if point_name is None or point_name == "":
            raise ValueError("Unknown point in room {}".format(room_name))
        if room_name is None or room_name == "":
            raise ValueError("Point {} to be added to unknown room".format(configuration))
        
        point_id = NAME_SEPARATOR + room_name + NAME_SEPARATOR + point_name
        
        ctlPin = configuration.get(CONFIG_POINT_CONTROLPIN)
        if ctlPin is None or ctlPin == "":
            raise ValueError("Point {} does not have {} defined".format(point_id, CONFIG_POINT_CONTROLPIN))
        btnPin = configuration.get(CONFIG_POINT_BUTTONPIN)
        if btnPin is None or btnPin == "":
            raise ValueError("Point {} does not have {} defined".format(point_id, CONFIG_POINT_BUTTONPIN))

        point_type = configuration.get(CONFIG_POINT_TYPE)
        if point_type == CONFIG_POINT_TYPE_LIGHT:
            point = LightPoint(id=point_id,
                controlPin=ctlPin,
                buttonPin=btnPin,
                comm_service=comm_service)
            point.initialize()
            return point
        elif point_type == CONFIG_POINT_TYPE_BLIND:
            point = BlindPoint(id=point_id,
                controlUpPin=ctlPin,
                controlDownPin=btnPin,
                comm_service=comm_service)
            point.initialize()
            return point
        else:
            raise ValueError("Unrecognized point type: {}".format(point_type))