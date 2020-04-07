from pyb import Pin, ExtInt, ADC, Timer,  delay
from pyb import disable_irq, enable_irq
from math import fabs, modf, trunc
from machine import I2C
from ssd1306 import SSD1306_I2C
from writer import Writer
import freesans20, font10
import micropython
from speed import Speed

class Button(object):
    def __init__(self):
        self.extint = ExtInt(Pin('ON/OFF'), ExtInt.IRQ_FALLING, Pin.PULL_UP, self.__callback__)
        self._status = False
        
    def __callback__(self, line):
        #print('1, button __callback__', line)
        self.extint.disable()
        delay(500)
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

class Display(object):
    def __init__(self):
        self.i2c = I2C(scl=Pin('SCL'), sda=Pin('SDA'))
        self.screen = SSD1306_I2C(128, 64, self.i2c)
        self.wrt = Writer(self.screen, freesans20, False),\
                   Writer(self.screen, font10, False)
        self._msg_ = 'Iniciando'
        self._data_ = None

        
    def set_msg(self, msg):
        irq_state = disable_irq()
        self._data_ = None
        self._msg_ = msg
        enable_irq(irq_state)
        #print('msg=',self._msg_)

    def set_data(self, data):
        irq_state = disable_irq()
        self._msg_ = None
        self._data_ = data
        enable_irq(irq_state)
        #print('data=', self._data_)
    
    def show_msg(self):
        if self._msg_ is None: return
        self.screen.fill(0)
        self.wrt[0].set_textpos(self.screen, 10, 0)
        self.wrt[0].printstring(self._msg_)
        self.screen.show()
        
    def show_data(self):
        if self._data_ is None: return
#        print(self._data_)
        speed, distance, duration = self._data_
        self.screen.fill(0)
        self.screen.hline(0, 32, 128, 2)
        self.screen.vline(68, 32, 32, 2)
    
        wpos = 10 if speed.ref >= 10 else 20
        self.wrt[0].set_textpos(self.screen, 5, wpos)
        if fabs(speed.delta) > 0.2:
            spd_msg = '[{0:.1f}] < {1:.1f}'.format(speed.ref, speed.act)
        else:
            spd_msg = '{:.1f} Km/h'.format(speed.ref)
        self.wrt[0].printstring(spd_msg)        

        km, m = divmod(int(distance),1000)
        dst_msg = '{:.1f} Km'.format(trunc(distance/100)/10) if km > 0 else '{:3d} m'.format(m)
        wrt = self.wrt[1] if km >= 10 else self.wrt[0]
        wrt.set_textpos(self.screen, 43 if km >= 10 else 40, 4)
        wrt.printstring(dst_msg)
        
        self.wrt[0].set_textpos(self.screen, 40, 75)
        h,s = divmod(int(duration),3600) # horas
        m,s = divmod(s,60) # minutos
        H,h = divmod(h, 10) # decenas de horas
        if H > 0: self.wrt[0].printstring('{:2d}:{:02d}'.format(h,m))
        else:
            self.wrt[0].printstring('{:02d}:{:02d}'.format(m,s) if h == 0 else '{:1d}h:{:02d}'.format(h,m))

        self.screen.show()
        
class Board(object):
    def __init__(self, speed_mngr, slope_mngr):
        self.switch = Button()
        self.buzzer = Buzzer()
        self.led = RGBLed()
        self.display = Display()
        self.speed_meter = speed_mngr.meter
        self.speed_leader = speed_mngr.leader
        self.slope_leader = slope_mngr.leader
#        self._timer = Timer(1, freq=1)
#        self._timer.callback(self.callback)
        
#    def callback(self, t):
#        micropython.schedule(self.show,0)

    def show(self):
        self.display.show_msg()
        self.display.show_data()
            
    def start(self):
        self.led.yellow()
        self.buzzer.beep(300)
        self.display.set_msg('Bajar\nControles!!')
        self.show()
        
    def isReady(self):
        return True if self.speed_leader.off() and self.slope_leader.off() else False
    
    def setReady(self):
        self.display.set_msg('Preparado?\nPulsar Boton!!')
        self.show()
        self.led.green()
        self.switch.reset()
        self.buzzer.beep()
        
    def isOn(self):
        return True if self.switch.on() else False

    def running(self):
        speed = Speed(self.speed_leader.speed, self.speed_meter.speed)
        self.display.set_data((speed, self.speed_meter.distance, self.speed_meter.duration))
        self.show()
        
    def setOn(self):
        self.display.set_msg('Iniciando!!')
        self.led.blue()
        self.buzzer.tbeep(300)
        self.show()

    def stopping(self):
        self.display.set_msg('Parando!!')
        self.show()
        self.led.red()
        self.buzzer.tbeep(500)
        
    def stopped(self):
        speed, distance, duration = self.speed_meter.sm_data
        self.display.set_data((Speed(speed,speed), distance, duration))
        self.show()
        self.led.green()
        self.buzzer.tbeep(1000)
        self.buzzer.silent()
        #print('stopped')
        
