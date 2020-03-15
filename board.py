from pyb import Pin, ExtInt, ADC, Timer, delay
from pyb import disable_irq, enable_irq

class Button(object):
    def __init__(self):
        self.extint = ExtInt(Pin('ON/OFF'), ExtInt.IRQ_FALLING, Pin.PULL_UP, self.__callback__)
        self._status = False
        
    def __callback__(self, line):
        #print('1, button __callback__', line)
        self.extint.disable()
        delay(200)
        self._status = False if self._status else True
        self.extint.enable()

    def reset(self):
        irq_state = disable_irq()
        self._status = False
        enable_irq(irq_state)
        
    def on(self):
        #print('switch status=', self._status)
        return True if self._status else False

class Buzzer(object):
    def __init__(self):
        self.pin = Pin('Buzzer')
        self.pin.high()
        
    def beep(self, span=100): # milisecons
        self.pin.low()
        delay(span)
        self.pin.high()

    def tbeep(self, span=100):
        for n in range(3): self.beep(span); delay(1000)

    def silent(self):
        self.pin.high()

class RGBLed(object):
    colors = ('red', 'blue', 'green', 'yellow', 'pink', 'marine')
    def __init__(self):
        self.pRed   = Pin('lRed')
        self.pGreen = Pin('lGreen')
        self.pBlue  = Pin('lBlue')
        self.color = None
        self.active = []
        
        self.timer = Timer(2, freq=1)
        self.timer.callback(self.__toggle__)
        self.off()

    def red(self):
        if self.color == 'red': return
        self.pGreen.low()
        self.pBlue.low()
        self.active.clear()
        self.active.append(self.pRed)
        self.color = 'red'

    def blue(self):
        if self.color == 'blue': return
        self.pRed.low()
        self.pGreen.low()
        self.active.clear()
        self.active.append(self.pBlue)
        self.color = 'blue'

    def green(self):
        if self.color == 'green': return
        self.pRed.low()
        self.pBlue.low()
        self.active.clear()
        self.active.append(self.pGreen)
        self.color = 'green'

    def yellow(self):
        if self.color == 'yellow': return
        self.off()
        self.active.append(self.pGreen)
        self.active.append(self.pRed)
        self.color = 'yellow'

    def pink(self):
        if self.color == 'pink': return
        self.off()
        self.active.append(self.pBlue)
        self.active.append(self.pRed)
        self.color = 'pink'

    def marine(self):
        if self.color == 'marine': return
        self.off()
        self.active.append(self.pGreen)
        self.active.append(self.pBlue)
        self.color = 'marine'
            
    def off(self):
        self.pRed.low()
        self.pGreen.low()
        self.pBlue.low()
        self.active.clear()

    def __toggle__(self, tim):
        if self.color is None: return
        for pin in self.active:
            pin.off() if pin.value() else pin.on()
        
class Board(object):
    def __init__(self, speed_mngr, slope_mngr):
        self.switch = Button()
        self.buzzer = Buzzer()
        self.led = RGBLed()
        self.speed_meter = speed_mngr.meter
        self.speed_leader = speed_mngr.leader
        self.slope_leader = slope_mngr.leader
        
    def start(self):
        self.led.yellow()
        self.buzzer.beep(300)
        
    def isReady(self):
        return True if self.speed_leader.off() and self.slope_leader.off() else False
    
    def setReady(self):
        #print('ready')
        self.led.green()
        self.switch.reset()
        self.buzzer.beep()
        
    def isOn(self):
        return True if self.switch.on() else False

    def setOn(self):
        #print('on')
        self.led.blue()
        self.buzzer.tbeep(300)

    def stopping(self):
        #print('stopping')
        self.led.red()
        self.buzzer.tbeep(500)
        
    def stopped(self):
        self.led.green()
        self.buzzer.tbeep(1000)
        self.buzzer.silent()
        #print('stopped')
        
