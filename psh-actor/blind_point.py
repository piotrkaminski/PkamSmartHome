from constants import COMMAND_ON
from constants import COMMAND_OFF
from constants import COMMAND_OPEN
from constants import COMMAND_1_4
from constants import COMMAND_1_2
from constants import COMMAND_3_4
from constants import COMMAND_CLOSED

from constants import POSITION_OPEN
from constants import POSITION_1_4
from constants import POSITION_1_2
from constants import POSITION_3_4
from constants import POSITION_CLOSED

from gpiozero import LED, Button, DigitalOutputDevice
from point import Point
from time import sleep
import logging

class BlindPoint(Point):

    def __init__(self, id, controlUpPin, controlDownPin, comm_service):
        Point.__init__(self, id=id, controlPin=None)
        self.controlUpPin = controlUpPin
        self.controlUpDevice = None
        self.controlDownPin = controlDownPin
        self.controlDownDevice = None
        self.comm_service = comm_service
        self.position = 0
        self.timeToCrossChunkSeconds = 1.0
        logging.info("Blind point {0} initialized, Ctn Up: {1}, Ctn Down: {2}, Pos: ".format(self.id, self.controlUpPin, self.controlDownPin, self.position))
    
    def initialize(self):
        self.controlUpDevice = DigitalOutputDevice(self.controlUpPin)
        self.controlDownDevice = DigitalOutputDevice(self.controlDownPin)

    def notifyCurrentState(self):
        message = None
        logging.info("Notify bind {id} state to {position}".format(id=self.id, position=self.position))
        if self.position == 0:
            message = COMMAND_OPEN
        elif self.position == 25:
            message = COMMAND_1_4
        elif self.position == 50:
            message = COMMAND_1_2
        elif self.position == 75:
            message = COMMAND_3_4
        elif self.position == 100:
            message = COMMAND_CLOSED
        self.comm_service.sendStatusUpdate(point_id=self.id, message=message)
    
    def updateStatus(self, message):
        logging.info("Apply {id} state to {message}".format(id=self.id, message=message))
        expected_pos = POSITION_OPEN
        if message == COMMAND_OPEN:
            expected_pos = POSITION_OPEN
        elif message == COMMAND_1_4:
            expected_pos = POSITION_1_4
        elif message == COMMAND_1_2:
            expected_pos = POSITION_1_2
        elif message == COMMAND_3_4:
            expected_pos = POSITION_3_4
        elif message == COMMAND_CLOSED:
            expected_pos = POSITION_CLOSED
        else:
            logging.error("Unrecognized command {cmd} for bind point {id}, skipped.".format(cmd=message, id=self.id))
            return
        
        delta = expected_pos - self.position
        if delta == 0:
            return 
        elif delta < 0:
            self.moveUp(delta)
        elif delta > 0:
            self.moveDown(delta)
        logging.info("Final {id} pos: {pos} ".format(id=self.id, pos=self.position))


    def calculateDistance(self, delta):
        # it is assumed POSITION_1_4 is smallest chunk
        chunksToMove = delta / POSITION_1_4 
        return chunksToMove * self.timeToCrossChunkSeconds


    def moveUp(self, delta):
        logging.info("Open blind, current pos: {pos} delta: {delta}".format(pos=self.position, delta=delta))
        self.controlUpDevice.blink(self.calculateDistance(delta), 0, 1, True)
        self.position += delta

    def moveDown(self, delta):
        logging.info("Close blind, current  pos: {pos} delta: {delta}".format(pos=self.position, delta=delta))
        self.controlDownDevice.blink(self.calculateDistance(delta), 0, 1, True)
        self.position += delta

    def reset(self):
        self.updateStatus(COMMAND_OPEN)
        self.notifyCurrentState()

    def enable(self):
        updateStatus(COMMAND_OPEN)
        logging.info("Enabled blind {0}".format(self.id))

    def disable(self):
        updateStatus(COMMAND_CLOSED)
        logging.info("Closed blind {0}".format(self.id))

    def toggle(self):
        return 