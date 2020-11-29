#!/usr/bin/env python3

import time

HAVE_BLINKY = False
HAVE_BLINKT = False

try:
    from multi_blinkt import blinky
    HAVE_BLINKY = True
except ImportError:
    pass    

try:
    from blinkt import set_pixel, set_brightness, show
    HAVE_BLINKT = True
except ImportError:
    pass


class Colors:
    @staticmethod
    def Black():
        return (0, 0, 0)
    @staticmethod
    def White():
        return (255, 255, 255)
    @staticmethod
    def Red():
        return (255, 0, 0)
    @staticmethod
    def Green():
        return (0, 255, 0)
    @staticmethod
    def GreenLow():
        return (0, 8, 0)
    @staticmethod
    def Blue():
        return (0, 0, 255)
    @staticmethod
    def Yellow():
        return (255, 128, 0) # Blinkt's green component is overpowered, reduce it to make it more clearly yellow


class LedInterfaceBase:
    def On(self, led_index, color):
        pass
    
    def Off(self, led_index):
        pass
   
    
class LedInterfaceBlinkt:
    def __init__(self):
        set_brightness(0.05)
    
    def On(self, led_index, color):
        r = color[0]
        g = color[1]
        b = color[2]
        set_pixel(led_index, r, g, b)
        show()
    
    def Off(self, led_index):
        set_pixel(led_index, 0, 0, 0)
        show()
        
        
class LedInterfaceBlinky:
    def __init__(self):
        self.led = blinky.Blinkt()
        self.result = ""
        
    def On(self, led_index, color):
        self.result = self.led.On(led_index, color)
        
    def Off(self, led_index):
        self.result = self.led.Off(led_index)


# change these if you wish to use other LEDs than the first (leftmost) ones
LED_COMMS = 0
LED_STATUS_FIRST = LED_COMMS + 1


class LedController:
    def __init__(self):
        if HAVE_BLINKY:
            self.interface = LedInterfaceBlinky()
            print("Using Blinky LED interface")
        elif HAVE_BLINKT:
            self.interface = LedInterfaceBlinkt()
            print("Using Blinkt LED interface")
        else:
            self.interface = LedInterfaceBase()
            print("No LED interface installed")

    def Interface(self):
        return self.interface

    def OnCommsStart(self):
        self.interface.On(LED_COMMS, Colors.Blue())
    
    def OnCommsEnd(self):
        self.interface.Off(LED_COMMS)
    
    def WaitWithCommsLedErrorBlinking(self, timeout):
        start = time.time()
        while (time.time() - start < timeout):
            self.interface.On(LED_COMMS, Colors.Red())
            time.sleep(0.5)
            self.interface.On(LED_COMMS, Colors.Blue())
            time.sleep(0.5)
            self.interface.Off(LED_COMMS)

    def WaitWithCommsLedGoodStateBlinking(self, timeout):
        start = time.time()
        while (time.time() - start < timeout):
            self.interface.On(LED_COMMS, Colors.Green())
            time.sleep(0.1)
            self.interface.Off(LED_COMMS)
            time.sleep(10)
    
    def ShowStatusLeds(self, colors):
        i = LED_STATUS_FIRST
        for color in colors:
            self.interface.On(i, color)
            i += 1
    
    def ClearAll(self):
        pass
        