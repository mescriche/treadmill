from pyb import Pin, ADC, Timer, delay
from math import fabs, trunc
from micropython import const

class SlopeLeader(object):
    def __init__(self):
        self.adc = ADC(Pin('rINC'))
        self._timer = Timer(7, freq=100)
        self._buffer = bytearray(10)

    def read(self):
        self.adc.read_timed(self._buffer, self._timer) # resolution 256 
        value = sum(self._buffer) // len(self._buffer)
        slope = value / 256 # ratio to cover
        return slope

    def off(self):
        #value = self.read()
        #print('slope=', value)
        return True if self.read() <= 0.1 else False

    
class SlopeController(object):
    SLOPE_TMAX = const(14000) #mseconds time for the motor to cover maximum inclination range
    N_LEVELS = const(5)
    def __init__(self):
        Pin('INC+').off()
        Pin('INC-').off()
        self._level_time = int(self.SLOPE_TMAX / self.N_LEVELS)
        self._t_increased = 0
        self._t_decreased = 0
        self._slope = 0
        self._rslope = 0

    def check(self, rslope): # ratio to cover
        self._rslope = int(self.SLOPE_TMAX * rslope) # mseconds
        self._slope = self._t_increased - self._t_decreased
        #print('rslope={}, slope={}'.format(self._rslope, self._slope))
        return False if fabs(self._rslope - self._slope) < self._level_time else True

    def execute(self):
        if self._rslope > self._slope:
            Pin('INC+').on()
            delay(self._level_time)
            Pin('INC+').off()
            self._t_increased += self._level_time
        elif self._rslope < self._slope:
            Pin('INC-').on()
            delay(self._level_time)
            Pin('INC-').off()
            self._t_decreased += self._level_time

    def get_down(self):
        self._slope = self._t_increased - self._t_decreased
        Pin('INC-').on()
        if self._slope > 0: delay(self._slope)
        delay(1000)
        Pin('INC-').off()
        self._t_decreased += self._slope

    
class SlopeManager(object):
    def __init__(self):
        self.leader = SlopeLeader()
        self.cntrl = SlopeController()

    def control(self):
        rslope = self.leader.read()
        if self.cntrl.check(rslope):
            self.cntrl.execute()

    def get_down(self):
        self.cntrl.get_down()
