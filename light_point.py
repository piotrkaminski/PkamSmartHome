from gpiozero import LED, Button
from point import Point
from time import sleep

def button_released(device):
    device.toggle()

class LightPoint(Point):

    def __init__(self, name, controlPin, buttonPin):
        Point.__init__(self, name=name, controlPin=controlPin)
        self.buttonPin = buttonPin
        self.button = Button(buttonPin)
        self.led = LED(controlPin)
        self.button.when_released = lambda: button_released(self)

    def notifyCurrentState(self):
        print("Light {name} state {state}".format(name=self.name, state=self.led.is_lit))
    
    def enable(self):
        self.led.on()

    def disable(self):
        self.led.off()


    def toggle(self):
        if self.led.is_lit:
            self.disable()
        else:
            self.enable()
        self.notifyCurrentState()