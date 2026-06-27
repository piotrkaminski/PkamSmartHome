from constants import CONFIG_POINT_NAME
from constants import CONFIG_POINT_TYPE
from constants import CONFIG_POINT_TYPE_LIGHT
from constants import CONFIG_POINT_TYPE_BLIND
from constants import CONFIG_POINT_CONTROLPIN
from constants import CONFIG_POINT_BUTTONPIN
from constants import CONFIG_POINT_CONTROLPIN_UP
from constants import CONFIG_POINT_CONTROLPIN_DOWN
from constants import CONFIG_POINT_BUTTONPIN_UP
from constants import CONFIG_POINT_BUTTONPIN_DOWN
from constants import CONFIG_POINT_FULL_TRAVEL_TIME
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

        point_type = configuration.get(CONFIG_POINT_TYPE)
        if point_type == CONFIG_POINT_TYPE_LIGHT:
            return self._createLightPoint(point_id, configuration, comm_service)
        elif point_type == CONFIG_POINT_TYPE_BLIND:
            return self._createBlindPoint(point_id, configuration, comm_service)
        else:
            raise ValueError("Unrecognized point type: {}".format(point_type))

    def _createLightPoint(self, point_id, configuration, comm_service):
        ctlPin = configuration.get(CONFIG_POINT_CONTROLPIN)
        if ctlPin is None or ctlPin == "":
            raise ValueError("Point {} does not have {} defined".format(point_id, CONFIG_POINT_CONTROLPIN))
        btnPin = configuration.get(CONFIG_POINT_BUTTONPIN)
        if btnPin is None or btnPin == "":
            raise ValueError("Point {} does not have {} defined".format(point_id, CONFIG_POINT_BUTTONPIN))

        point = LightPoint(id=point_id,
            controlPin=ctlPin,
            buttonPin=btnPin,
            comm_service=comm_service)
        point.initialize()
        return point

    def _createBlindPoint(self, point_id, configuration, comm_service):
        ctlPinUp = configuration.get(CONFIG_POINT_CONTROLPIN_UP)
        if ctlPinUp is None or ctlPinUp == "":
            raise ValueError("Point {} does not have {} defined".format(point_id, CONFIG_POINT_CONTROLPIN_UP))
        ctlPinDown = configuration.get(CONFIG_POINT_CONTROLPIN_DOWN)
        if ctlPinDown is None or ctlPinDown == "":
            raise ValueError("Point {} does not have {} defined".format(point_id, CONFIG_POINT_CONTROLPIN_DOWN))
        btnPinUp = configuration.get(CONFIG_POINT_BUTTONPIN_UP)
        if btnPinUp is None or btnPinUp == "":
            raise ValueError("Point {} does not have {} defined".format(point_id, CONFIG_POINT_BUTTONPIN_UP))
        btnPinDown = configuration.get(CONFIG_POINT_BUTTONPIN_DOWN)
        if btnPinDown is None or btnPinDown == "":
            raise ValueError("Point {} does not have {} defined".format(point_id, CONFIG_POINT_BUTTONPIN_DOWN))
        fullTravelTime = configuration.get(CONFIG_POINT_FULL_TRAVEL_TIME)
        if fullTravelTime is None or fullTravelTime == "":
            raise ValueError("Point {} does not have {} defined".format(point_id, CONFIG_POINT_FULL_TRAVEL_TIME))

        point = BlindPoint(id=point_id,
            controlPinUp=ctlPinUp,
            controlPinDown=ctlPinDown,
            buttonPinUp=btnPinUp,
            buttonPinDown=btnPinDown,
            fullTravelTimeSec=fullTravelTime,
            comm_service=comm_service)
        point.initialize()
        return point