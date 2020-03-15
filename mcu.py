from pyb import LED, Timer, rng, disable_irq, enable_irq
def randint(min, max):
    span = max - min + 1
    div = 0x3fffffff // span
    offset = rng() // div
    val = min + offset
    return val

class MCU(object):
    # LED led(1)=green, led(2)=blue, led(3)=yellow, led(4)=red
    # leds [0=green, 1=blue, 2=yellow, 3=red]
    colors = ('green', 'blue', 'yellow', 'red')
    mode = ('deterministic', 'random')
    
    def __init__(self):
        self._timer = Timer(8, freq=1)
        self._leds = [LED(i) for i in range(1,5)]
        self._color = 'yellow'
        self._timer.callback(self._callback_)
        self._mode = False #'deterministic'
        self._led = self._leds[0]
        self._status = False

    def _callback_(self, tim):
        self._status = False if self._status else True
        id = randint(0,3) if self._mode is True \
             else self.colors.index(self._color)
        led = self._leds[id]
        if led != self._led: self._led.off(); self._led = led
        self._led.on() if self._status else self._led.off()
        
    def _set_color(self, color):
        if self._color != color:
            n = self.colors.index(self._color)
            self._leds[n].off()
        self._color = color
        
    def yellow(self):
        self._set_color('yellow')
        
    def green(self):
        self._set_color('green')
            
    def blue(self):
        self._set_color('blue')
        
    def red(self):
        self._set_color('red')

    def random(self, mode=True):
        status = disable_irq()
        self._mode = mode
        enable_irq()

    
