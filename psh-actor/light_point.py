from constants import COMMAND_ON
from constants import COMMAND_OFF

from gpiozero import LED, Button
from point import Point
from time import sleep

def button_released(device):
    device.toggle()

class LightPoint(Point):

    def __init__(self, id, controlPin, buttonPin, comm_service):
        Point.__init__(self, id=id, controlPin=controlPin)
        self.buttonPin = buttonPin
        self.button = Button(buttonPin)
        self.led = LED(controlPin)
        self.button.when_released = lambda: button_released(self)
        self.comm_service = comm_service

    def notifyCurrentState(self):
        message = None
        print("Light {id} state {state}".format(id=self.id, state=self.led.is_lit))
        if self.led.is_lit:
            message = COMMAND_ON
        else:
            message = COMMAND_OFF
        self.comm_service.sendStatusUpdate(point_id=self.id, message=message)
    
    def updateStatus(self, point_id, message):
        if message == COMMAND_OFF:
            self.disable()
        else:
            if message == COMMAND_ON:
                self.enable()
            else:
                print("Unrecognized command {cmd} for point {id}, skipped.".format(cmd=message, id=self.id))

    def enable(self):
        self.led.on()
        print("Enabled point {0}".format(self.id))

    def disable(self):
        self.led.off()
        print("Disabled point {0}".format(self.id))

    def toggle(self):
        if self.led.is_lit:
            self.disable()
        else:
            self.enable()
        self.notifyCurrentState()