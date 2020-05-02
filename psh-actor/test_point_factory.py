from point_factory import PointFactory
from point import Point
from unittest import TestCase
from unittest.mock import Mock

class PointFactoryTest(TestCase):

    def setUp(self):
        self.point_factory = PointFactory()

    def test_create_point_success(self):
        conf = {
                    "Name": "Ceiling",
                    "Type": "Light",
                    "GpioControlPin": 17,
                    "GpioButtonPin": 2
                }
        room_name = "RoomU"
        comm_service = Mock()
        point = self.point_factory.createPoint(
            room_name=room_name, 
            configuration=conf, 
            comm_service=comm_service)
        self.assertEqual("/RoomU/Ceiling", point.id)
        self.assertEqual(17, point.controlPin)
        self.assertEqual(2, point.buttonPin)
        self.assertIsNotNone(point.button)
        self.assertEqual(point.buttonPin, point.button.pin.number)
        self.assertIsNotNone(point.led)
        self.assertEqual(point.controlPin, point.led.pin.number)

    def test_create_point_no_name(self):
        conf = {
                    "Type": "Light",
                    "GpioControlPin": 18,
                    "GpioButtonPin": 3
                }
        room_name = "RoomU"
        comm_service = Mock()
        self.assertRaises(ValueError,lambda: self.point_factory.createPoint(
            room_name=room_name, 
            configuration=conf, 
            comm_service=comm_service))

    def test_create_point_no_room_name(self):
        conf = {
                    "Name": "Ceiling",
                    "Type": "Light",
                    "GpioControlPin": 17,
                    "GpioButtonPin": 2
                }
        room_name = None
        comm_service = Mock()
        self.assertRaises(ValueError,lambda: self.point_factory.createPoint(
            room_name=room_name, 
            configuration=conf, 
            comm_service=comm_service))
        room_name = ""
        self.assertRaises(ValueError,lambda: self.point_factory.createPoint(
            room_name=room_name, 
            configuration=conf, 
            comm_service=comm_service))

    def test_create_point_no_type(self):
        conf = {
                    "Name": "Ceiling",
                    "Type": "LightERT",
                    "GpioControlPin": 17,
                    "GpioButtonPin": 2
                }
        room_name = "RoomW"
        comm_service = Mock()
        self.assertRaises(ValueError,lambda: self.point_factory.createPoint(
            room_name=room_name, 
            configuration=conf, 
            comm_service=comm_service))
        
        conf = {
                    "Name": "Ceiling",
                    "Type": "",
                    "GpioControlPin": 17,
                    "GpioButtonPin": 2
                }
        self.assertRaises(ValueError,lambda: self.point_factory.createPoint(
            room_name=room_name, 
            configuration=conf, 
            comm_service=comm_service))
        
        conf = {
                    "Name": "Ceiling",
                    "GpioControlPin": 17,
                    "GpioButtonPin": 2
                }
        self.assertRaises(ValueError,lambda: self.point_factory.createPoint(
            room_name=room_name, 
            configuration=conf, 
            comm_service=comm_service))

    def test_create_point_no_controlPin(self):
        conf = {
                    "Name": "Ceiling",
                    "Type": "Light",
                    "GpioControlPin": "",
                    "GpioButtonPin": 2
                }
        room_name = "RoomW"
        comm_service = Mock()
        self.assertRaises(ValueError,lambda: self.point_factory.createPoint(
            room_name=room_name, 
            configuration=conf, 
            comm_service=comm_service))
        
        conf = {
                    "Name": "Ceiling",
                    "Type": "Light",
                    "GpioButtonPin": 2
                }
        self.assertRaises(ValueError,lambda: self.point_factory.createPoint(
            room_name=room_name, 
            configuration=conf, 
            comm_service=comm_service))

    def test_create_point_no_buttonPin(self):
        conf = {
                    "Name": "Ceiling",
                    "Type": "Light",
                    "GpioControlPin": 17,
                    "GpioButtonPin": ""
                }
        room_name = "RoomW"
        comm_service = Mock()
        self.assertRaises(ValueError,lambda: self.point_factory.createPoint(
            room_name=room_name, 
            configuration=conf, 
            comm_service=comm_service))
        
        conf = {
                    "Name": "Ceiling",
                    "Type": "Light",
                    "GpioControlPin": 17,
                }
        self.assertRaises(ValueError,lambda: self.point_factory.createPoint(
            room_name=room_name, 
            configuration=conf, 
            comm_service=comm_service))