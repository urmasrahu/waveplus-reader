USE_BLINKT = False

try:
    from blinkt import set_pixel, set_brightness, show
    import time
    USE_BLINKT = True
    print ("Using Blinkt LED strip to show status")
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


# change these if you wish to use other LEDs than the first (leftmost) ones
LED_COMMS = 0
LED_STATUS_FIRST = LED_COMMS + 1


class LedController:
    def __init__(self):
        self.interface = LedInterfaceBlinkt() if USE_BLINKT else LedInterfaceBase();

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
        