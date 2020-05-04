from rooms_service import RoomsService
from room import Room
from unittest import TestCase
from unittest.mock import Mock

class RoomsServiceTest(TestCase):

    def test_get_room_name_success(self):
        service = RoomsService()
        self.assertEqual("RoomX", service.get_room_name("/RoomX/PointDFS"))
        self.assertEqual("Room1", service.get_room_name("/Room1/Point1"))
        self.assertEqual("Room1", service.get_room_name("/Room1/Point1/SubPoint"))
        

    def test_get_room_name_none(self):
        service = RoomsService()
        self.assertEqual(None, service.get_room_name("Room1"))
        self.assertEqual(None, service.get_room_name("/Room1"))

    def test_update_status_sucess(self):
        service = RoomsService()
        room_mock = Room("Room1")
        room_mock.updateStatus = Mock()
        service.rooms = [room_mock]
        service.updateStatus(point_id="/Room1/Point1", message="ON")
        room_mock.updateStatus.assert_called()

    def test_update_status_no_room_with_name(self):
        service = RoomsService()
        room_mock = Room("RoomXX")
        room_mock.updateStatus = Mock()
        service.rooms = [room_mock]
        service.updateStatus(point_id="/Room1/Point1", message="ON")
        room_mock.updateStatus.assert_not_called()

    def test_update_status_none_room_name(self):
        service = RoomsService()
        room_mock = Room("RoomXX")
        room_mock.updateStatus = Mock()
        service.rooms = [room_mock]
        service.updateStatus(point_id="/Room1", message="ON")
        room_mock.updateStatus.assert_not_called()

        service.updateStatus(point_id=None, message="ON")
        room_mock.updateStatus.assert_not_called()

    def test_initialize_sucess(self):
        conf = {
            "Rooms": [
                {
                    "Name": "Office",
                    "Points": []
                }, {
                    "Name": "LivingRoom",
                    "Points": []
                }
            ]
        }
        service = RoomsService()
        service.initialize(configuration=conf, comm_service=None)
        self.assertEqual(2, len(service.rooms))
        self.assertEqual("Office", service.rooms[0].name)
        self.assertEqual("LivingRoom", service.rooms[1].name)

    def test_initalize_empty_config(self):
        conf = {}
        service = RoomsService()
        service.initialize(configuration=conf, comm_service=None)
        self.assertEqual(0, len(service.rooms))   

    
    def test_initalize_none_config(self):
        service = RoomsService()
        service.initialize(configuration=None, comm_service=None) 
        self.assertEqual(0, len(service.rooms))   

    def test_reset(self):
        service = RoomsService()
        room1 = Mock()
        room2 = Mock()
        service.rooms.append(room1)
        service.rooms.append(room2)

        service.reset()

        room1.reset.assert_called()
        room2.reset.assert_called()   