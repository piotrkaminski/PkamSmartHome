from light_point import LightPoint
from point import Point
from unittest import TestCase
from unittest.mock import Mock

class LightPointTest(TestCase):

    def test_notifyCurrentState_On(self):
        comm_srv = Mock()
        led = Mock()
        led.value = 1
        point = LightPoint(
            id="/RoomB/PointYU", 
            controlPin=1, 
            buttonPin=2, 
            comm_service=comm_srv)
        point.led = led

        point.notifyCurrentState()

        comm_srv.sendStatusUpdate.assert_called_with(point_id="/RoomB/PointYU", message="ON")

    def test_notifyCurrentState_Off(self):
        comm_srv = Mock()
        led = Mock()
        led.value = 0
        point = LightPoint(
            id="/RoomB/PointYU", 
            controlPin=3, 
            buttonPin=4, 
            comm_service=comm_srv)
        point.led = led

        point.notifyCurrentState()

        comm_srv.sendStatusUpdate.assert_called_with(point_id="/RoomB/PointYU", message="OFF")
    
    def test_updateStatus_On(self):
        led = Mock()
        point = LightPoint(
            id="/RoomB/PointYU", 
            controlPin=5, 
            buttonPin=6, 
            comm_service=None)
        point.led = led

        point.updateStatus(point_id=None, message="ON")

        led.on.assert_called()

    def test_updateStatus_Off(self):
        led = Mock()
        point = LightPoint(
            id="/RoomB/PointYU", 
            controlPin=7, 
            buttonPin=8, 
            comm_service=None)
        point.led = led

        point.updateStatus(point_id=None, message="ON")

        led.on.assert_called()

    def test_updateStatus_Any(self):
        led = Mock()
        point = LightPoint(
            id="/RoomB/PointYU", 
            controlPin=9, 
            buttonPin=10, 
            comm_service=None)
        point.led = led

        point.updateStatus(point_id=None, message="AnyMessage")

        led.on.assert_not_called()


    def test_enable(self):
        led = Mock()
        point = LightPoint(
            id="/RoomB/PointYU", 
            controlPin=11, 
            buttonPin=12, 
            comm_service=None)
        point.led = led

        point.enable()

        led.on.assert_called()
        led.off.assert_not_called()

    def test_disable(self):
        led = Mock()
        point = LightPoint(
            id="/RoomB/PointYU", 
            controlPin=13, 
            buttonPin=14, 
            comm_service=None)
        point.led = led

        point.disable()

        led.off.assert_called()
        led.on.assert_not_called()

    def test_toggle_to_off(self):
        led = Mock()
        led.value = 1
        comm_srv = Mock()
        point = LightPoint(
            id="/RoomB/PointYU", 
            controlPin=15, 
            buttonPin=16, 
            comm_service=comm_srv)
        point.led = led

        point.toggle()

        led.off.assert_called()
        led.on.assert_not_called()
        comm_srv.sendStatusUpdate.assert_called()

    def test_toggle_to_on(self):
        led = Mock()
        led.value = 0
        comm_srv = Mock()
        point = LightPoint(
            id="/RoomB/PointYU", 
            controlPin=17, 
            buttonPin=18, 
            comm_service=comm_srv)
        point.led = led

        point.toggle()

        led.off.assert_not_called()
        led.on.assert_called()
        comm_srv.sendStatusUpdate.assert_called()