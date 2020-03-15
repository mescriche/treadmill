from pyb import Pin, ADC, Timer, delay, ExtInt, disable_irq, enable_irq
from time import ticks_ms, ticks_us, ticks_diff, ticks_add
from math import fabs, pow
from array import array
from micropython import const

import micropython
micropython.alloc_emergency_exception_buf(100)

class SpeedLeader(object):
    M_MAX = const(10)
    SPD_MAX = const(15) # 15 km/h
    def __init__(self):
        self._adc = ADC(Pin('rSPD'))
        self._timer = Timer(6, freq=100)
        self._buffer = bytearray(self.M_MAX)
        
    def read(self):
        self._adc.read_timed(self._buffer, self._timer) # resolution 256 
        value = sum(self._buffer) // len(self._buffer)
        speed = value * self.SPD_MAX / 256 #[km/h] 
        return speed

    def off(self):
        value = self.read()
        #print('speed=', value)
        return True if value <= 2.0 else False

class SpeedMeter(object):
    BUFFER_SIZE = const(6)
    WEIGHTS = (const(0.5), const(0.25), const(0.125), const(0.0625), const(0.0625))
    KFREQ = 0.22 * 3.6 # km/h
    def __init__(self):
        self._sample_times = array('L', 0 for i in range(self.BUFFER_SIZE))
        self.extint =ExtInt(Pin('SPD'), ExtInt.IRQ_FALLING, Pin.PULL_UP, self.__callback__)
        self.freq = 0

    def __callback__(self, line):
        for i in range(self.BUFFER_SIZE-1, 0, -1):
            self._sample_times[i]=self._sample_times[i-1]
        else: self._sample_times[0] = ticks_ms()

    def read(self):
        irq_state = disable_irq()
        periods = [ticks_diff(self._sample_times[i], self._sample_times[i+1])\
                   for i in range(self.BUFFER_SIZE-1)]
        #print('periods',end='=')
        #for item in periods: print(item, end=',')
        self.period = sum([x*y for x,y in zip(self.WEIGHTS, periods)]) * pow(10,-3) #seconds
        try: self.freq = 1/self.period
        except: self.freq = 0
        self.speed = self.freq * self.KFREQ #km/h
        enable_irq(irq_state)
        #print('period[s]={:.3f}, freq[Hz]={:.1f}, speed[km/h]={:1f}'.format(self.period, self.freq, self.speed))
        return self.speed
        
        
class SpeedController(object):
    IW_LAPSE = const(1000) # increasing speed waiting lapse
    DW_LAPSE = const(300)  # decreasing speed waiting lapse
    
    def __init__(self):
        self.__last_action_time = 0
        self.__lapse = 0
        Pin('SPD+').off()
        Pin('SPD-').off()
        self._rspeed = 0
        self._mspeed = 0
        #Pin('S/W').on()
        
    def check(self, rspeed, mspeed):
        self.__lapse = ticks_diff(ticks_ms(), self.__last_action_time)
        if self.__lapse < self.IW_LAPSE and self.__lapse < self.DW_LAPSE : return False
        #print('rspeed[km/h]={:.1f} mspeed[km/h]={:.1f}'.format(self._rspeed, self._mspeed))
        if fabs(round(rspeed - mspeed,2)) < 0.10: return False
        self._rspeed = rspeed
        self._mspeed = mspeed
        return True

    def execute(self): #leader speed, measured speed
        if self._rspeed > self._mspeed and self.__lapse > self.IW_LAPSE:
            Pin('SPD+').on() # start increasing speed
            delay(1000)
            Pin('SPD+').off() # stop increasing speed
            self.__last_action_time = ticks_ms()
        elif self._rspeed < self._mspeed  and self.__lapse > self.DW_LAPSE:
            Pin('SPD-').on() # start decreasing speed
            delay(1000)
            Pin('SPD-').off() # start decreasing speed
            self.__last_action_time = ticks_ms()

    def slow_down(self):
        Pin('SPD-').on()
        delay(1000)
        Pin('SPD-').off()
        delay(self.DW_LAPSE)
        
    def start(self):
        Pin('S/W').on()
        
    def stop(self):
        Pin('S/W').off()

class SpeedManager(object):
    def __init__(self):
        self.leader = SpeedLeader()
        self.meter = SpeedMeter()
        self.cntrl = SpeedController()

    def start(self):
        self.cntrl.start()
        
    def control(self):
        rspeed = self.leader.read() #get reference speed
        mspeed = self.meter.read()  #get actual speed
        if self.cntrl.check(rspeed, mspeed): # check speed difference
            self.cntrl.execute() # take action to reduce speed difference

    def slow_down(self):
        while self.meter.read() > 2.0:
            self.cntrl.slow_down()

    def stop(self):
        self.cntrl.stop()
    
