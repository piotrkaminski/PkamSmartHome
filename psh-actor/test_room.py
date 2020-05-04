from room import Room
from point import Point
from unittest import TestCase
from unittest.mock import Mock

class RoomsTest(TestCase):

    def test_update_status_sucess(self):
        room = Room("Room1")
        point1_mock = Mock()
        point1_mock.id = "/Room1/Point1"
        point2_mock = Mock()
        point2_mock.id = "/Room1/Point2"
        room.points.append(point1_mock)
        room.points.append(point2_mock)
        room.updateStatus(point_id="/Room1/Point1", message="ON")
        point1_mock.updateStatus.assert_called()
        point2_mock.updateStatus.assert_not_called()

    def test_update_status_no_point_with_name(self):
        room = Room("Room1")
        point1_mock = Mock()
        point1_mock.id = "/Room1/Point1"
        point2_mock = Mock()
        point2_mock.id = "/Room1/Point2"
        room.points.append(point1_mock)
        room.points.append(point2_mock)
        room.updateStatus(point_id="/Room1/Point3", message="ON")
        point1_mock.updateStatus.assert_not_called()
        point2_mock.updateStatus.assert_not_called()

    def test_update_status_none_point_id(self):
        room = Room("Room1")
        point1_mock = Mock()
        point1_mock.id = "/Room1/Point1"
        point2_mock = Mock()
        point2_mock.id = "/Room1/Point2"
        room.points.append(point1_mock)
        room.points.append(point2_mock)
        room.updateStatus(point_id=None, message=None)
        point1_mock.updateStatus.assert_not_called()
        point2_mock.updateStatus.assert_not_called()

    def test_initialize_sucess(self):
        conf = [{
                    "Name": "Ceiling",
                    "Type": "Light",
                    "GpioControlPin": 22,
                    "GpioButtonPin": 23
                },{
                    "Name": "BackLight",
                    "Type": "Light",
                    "GpioControlPin": 24,
                    "GpioButtonPin": 25
                }]
        room = Room("Room")
        room.initialize(configuration=conf, comm_service=None)
        self.assertEqual(2, len(room.points))
        self.assertEqual("/Room/Ceiling", room.points[0].id)
        self.assertEqual("/Room/BackLight", room.points[1].id)

    def test_initalize_empty_config(self):
        conf = {}
        room = Room("Room1")
        room.initialize(configuration=conf, comm_service=None)
        self.assertEqual(0, len(room.points))   

    
    def test_initalize_none_config(self):
        room = Room("Room1")
        room.initialize(configuration=None, comm_service=None) 
        self.assertEqual(0, len(room.points))   

    def test_reset(self):
        room = Room("Room1")
        point1 = Mock()
        point2 = Mock()
        room.points.append(point1)
        room.points.append(point2) 

        room.reset()

        point1.reset.assert_called()
        point2.reset.assert_called() 