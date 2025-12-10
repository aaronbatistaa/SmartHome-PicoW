from machine import Pin

class Led:
    """Actuador LED ON/OFF."""

    def __init__(self, pin_num):
        self._pin = Pin(pin_num, Pin.OUT)
        self.off()

    def on(self):
        self._pin.value(1)

    def off(self):
        self._pin.value(0)


class Buzzer:
    """Actuador buzzer simple ON/OFF."""

    def __init__(self, pin_num):
        self._pin = Pin(pin_num, Pin.OUT)
        self.off()

    def on(self):
        self._pin.value(1)

    def off(self):
        self._pin.value(0)
