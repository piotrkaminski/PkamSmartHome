from constants import COMMAND_UP
from constants import COMMAND_DOWN
from constants import COMMAND_STOP

from gpiozero import Button, DigitalOutputDevice
from point import Point
from time import sleep, time
import threading
import logging

class BlindPoint(Point):

    INTERLOCK_DELAY_SEC = 0.5

    def __init__(self, id, controlPinUp, controlPinDown,
                 buttonPinUp, buttonPinDown, fullTravelTimeSec, comm_service):
        Point.__init__(self, id=id, controlPin=controlPinUp)
        self.controlPinUp = controlPinUp
        self.controlPinDown = controlPinDown
        self.buttonPinUp = buttonPinUp
        self.buttonPinDown = buttonPinDown
        self.fullTravelTimeSec = fullTravelTimeSec
        self.comm_service = comm_service
        self.relayUp = None
        self.relayDown = None
        self.buttonUp = None
        self.buttonDown = None
        self.position = 0.0
        self._movementTimer = None
        self._movementStartTime = None
        self._movementDirection = None
        logging.info("Blind point {0} initialized, CtlUp: {1}, CtlDown: {2}, BtnUp: {3}, BtnDown: {4}, Travel: {5}s"
            .format(self.id, self.controlPinUp, self.controlPinDown,
                    self.buttonPinUp, self.buttonPinDown, self.fullTravelTimeSec))

    def initialize(self):
        self.relayUp = DigitalOutputDevice(self.controlPinUp)
        self.relayDown = DigitalOutputDevice(self.controlPinDown)
        self.buttonUp = Button(pin=self.buttonPinUp, hold_time=0.1)
        self.buttonDown = Button(pin=self.buttonPinDown, hold_time=0.1)
        self.buttonUp.when_pressed = self._onButtonUpPressed
        self.buttonUp.when_released = self._onButtonUpReleased
        self.buttonDown.when_pressed = self._onButtonDownPressed
        self.buttonDown.when_released = self._onButtonDownReleased

    def notifyCurrentState(self):
        message = str(int(round(self.position)))
        logging.info("Notify blind {id} position: {pos}%".format(id=self.id, pos=message))
        self.comm_service.sendStatusUpdate(point_id=self.id, message=message)

    def updateStatus(self, message):
        if message == COMMAND_UP:
            self.moveUp()
        elif message == COMMAND_DOWN:
            self.moveDown()
        elif message == COMMAND_STOP:
            self.stop()
        else:
            try:
                targetPosition = float(message)
                if 0.0 <= targetPosition <= 100.0:
                    self.moveToPosition(targetPosition)
                else:
                    logging.error("Position {pos} out of range [0-100] for blind {id}, skipped."
                        .format(pos=message, id=self.id))
            except ValueError:
                logging.error("Unrecognized command {cmd} for blind {id}, skipped."
                    .format(cmd=message, id=self.id))

    def reset(self):
        self.stop()
        self.moveToPosition(0.0)

    def moveUp(self):
        self._cancelTimer()
        wasMovingDown = self._movementDirection == "down"
        self._stopRelays()
        if wasMovingDown:
            sleep(self.INTERLOCK_DELAY_SEC)
        if self.position <= 0.0:
            logging.info("Blind {id} already fully open, ignoring UP".format(id=self.id))
            return
        self._movementDirection = "up"
        self._movementStartTime = time()
        self.relayUp.on()
        logging.info("Blind {id} moving UP from {pos}%".format(id=self.id, pos=int(self.position)))

    def moveDown(self):
        self._cancelTimer()
        wasMovingUp = self._movementDirection == "up"
        self._stopRelays()
        if wasMovingUp:
            sleep(self.INTERLOCK_DELAY_SEC)
        if self.position >= 100.0:
            logging.info("Blind {id} already fully closed, ignoring DOWN".format(id=self.id))
            return
        self._movementDirection = "down"
        self._movementStartTime = time()
        self.relayDown.on()
        logging.info("Blind {id} moving DOWN from {pos}%".format(id=self.id, pos=int(self.position)))

    def stop(self):
        self._cancelTimer()
        self._updatePosition()
        self._stopRelays()
        self._movementDirection = None
        self._movementStartTime = None
        logging.info("Blind {id} stopped at {pos}%".format(id=self.id, pos=int(self.position)))
        self.notifyCurrentState()

    def moveToPosition(self, targetPosition):
        self._cancelTimer()
        self._updatePosition()
        self._stopRelays()

        delta = targetPosition - self.position
        if abs(delta) < 0.5:
            logging.info("Blind {id} already at target {pos}%".format(id=self.id, pos=int(targetPosition)))
            self.notifyCurrentState()
            return

        duration = abs(delta) / 100.0 * self.fullTravelTimeSec

        if delta < 0:
            wasMovingDown = self._movementDirection == "down"
            self._movementDirection = "up"
            if wasMovingDown:
                sleep(self.INTERLOCK_DELAY_SEC)
            self._movementStartTime = time()
            self.relayUp.on()
        else:
            wasMovingUp = self._movementDirection == "up"
            self._movementDirection = "down"
            if wasMovingUp:
                sleep(self.INTERLOCK_DELAY_SEC)
            self._movementStartTime = time()
            self.relayDown.on()

        logging.info("Blind {id} moving to {target}% (duration: {dur:.1f}s)"
            .format(id=self.id, target=int(targetPosition), dur=duration))
        self._movementTimer = threading.Timer(duration, self._onTimerExpired, args=[targetPosition])
        self._movementTimer.start()

    def _stopRelays(self):
        self.relayUp.off()
        self.relayDown.off()

    def _updatePosition(self):
        if self._movementStartTime is None or self._movementDirection is None:
            return
        elapsed = time() - self._movementStartTime
        delta = elapsed / self.fullTravelTimeSec * 100.0
        if self._movementDirection == "up":
            self.position = max(0.0, self.position - delta)
        elif self._movementDirection == "down":
            self.position = min(100.0, self.position + delta)

    def _onTimerExpired(self, targetPosition):
        self._stopRelays()
        self.position = targetPosition
        self._movementDirection = None
        self._movementStartTime = None
        self._movementTimer = None
        logging.info("Blind {id} reached target {pos}%".format(id=self.id, pos=int(targetPosition)))
        self.notifyCurrentState()

    def _cancelTimer(self):
        if self._movementTimer is not None:
            self._movementTimer.cancel()
            self._movementTimer = None

    def _onButtonUpPressed(self):
        self.moveUp()

    def _onButtonUpReleased(self):
        if self._movementDirection == "up":
            self.stop()

    def _onButtonDownPressed(self):
        self.moveDown()

    def _onButtonDownReleased(self):
        if self._movementDirection == "down":
            self.stop()
