from rooms_service import RoomsService
from unittest import TestCase

class RoomsServiceTest(TestCase):

    def test_get_room_name_success(self):
        service = RoomsService()
        self.assertEqual("RoomX",service.get_room_name("/RoomX/PointDFS"))
        self.assertEqual("Room1",service.get_room_name("/Room1/Point1"))
        self.assertEqual("Room1",service.get_room_name("/Room1/Point1/SubPoint"))
        self.assertEqual(None,service.get_room_name("Room1"))