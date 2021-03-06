from constants import COMMAND_ON
from constants import COMMAND_OFF

from gpiozero import LED, Button, DigitalOutputDevice
from point import Point
from time import sleep
import logging

class LightPoint(Point):

    def __init__(self, id, controlPin, buttonPin, comm_service):
        Point.__init__(self, id=id, controlPin=controlPin)
        self.buttonPin = buttonPin
        self.button = None
        self.led = None
        self.comm_service = comm_service
        logging.info("Light point {0} initialized, Ctn: {1}, Btn: {2}".format(self.id, self.controlPin, self.buttonPin))
    
    def initialize(self):
        self.button = Button(pin=self.buttonPin, hold_time=0.1)
        self.button.when_held = self.toggle
        self.led = DigitalOutputDevice(self.controlPin)

    def notifyCurrentState(self):
        message = None
        logging.info("Notify light {id} state to {state}".format(id=self.id, state=self.led.value))
        if self.led.value == 1:
            message = COMMAND_ON
        else:
            message = COMMAND_OFF
        self.comm_service.sendStatusUpdate(point_id=self.id, message=message)
    
    def updateStatus(self, message):
        if message == COMMAND_OFF:
            self.disable()
        else:
            if message == COMMAND_ON:
                self.enable()
            else:
                logging.error("Unrecognized command {cmd} for point {id}, skipped.".format(cmd=message, id=self.id))

    def reset(self):
        self.updateStatus(COMMAND_OFF)
        self.notifyCurrentState()

    def enable(self):
        self.led.on()
        logging.info("Enabled point {0}".format(self.id))

    def disable(self):
        self.led.off()
        logging.info("Disabled point {0}".format(self.id))

    def toggle(self):
        if self.led.value == 1:
            self.disable()
        else:
            self.enable()
        self.notifyCurrentState()