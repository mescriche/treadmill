from pyb import Pin, ADC, Timer, delay, ExtInt, disable_irq, enable_irq
from time import ticks_ms, ticks_us, ticks_diff, ticks_add
from math import fabs, pow, trunc
from array import array
from micropython import const

import micropython
micropython.alloc_emergency_exception_buf(100)

class Speed(object):
    def __init__(self,ref=0, act=0):
        self.ref = ref # reference value
        self.act = act # actual value
    @property
    def delta(self):
        return self.ref - self.act
    def __str__(self):
        return '{0:.1f}-{1:.1f}'.format(self.ref, self.act)
    def __repr__(self):
        return '{0:.1f}-{1:.1f}'.format(self.ref, self.act)
    
class SpeedLeader(object):
    M_MAX = const(20)
    SPD_MAX = const(15) # 15 km/h
    def __init__(self):
        self._adc = ADC(Pin('rSPD'))
        self._timer = Timer(6, freq=100)
        self._buffer = bytearray(self.M_MAX)

    @property
    def speed(self):
        self._adc.read_timed(self._buffer, self._timer) # resolution 256
        value = sum(self._buffer) // len(self._buffer)
        speed = value * self.SPD_MAX / 256 #[km/h]
        speed = trunc(speed * 10) / 10
        #print('ref speed=', speed)
        return speed

    def off(self):
        value = self.speed
        return True if value <= 2.0 else False

class SpeedMeter(object):
    STEP = 0.20 + 0.02 #const(6.5 * math.pi / 100) # meters - wheel circunference 2*pi*r + 2mm 
    BUFFER_SIZE = const(6)
    WEIGHTS = (0.4, 0.3, 0.2, 0.07, 0.03)

    def __init__(self):
        self._sample_times = array('L', 0 for i in range(self.BUFFER_SIZE))
        self.extint = ExtInt(Pin('SPD'), ExtInt.IRQ_FALLING, Pin.PULL_UP, self.__callback__)
        self.reset()
        
    def reset(self):
        self.counter = 0
        self.end_counter = None
        self.start_time = ticks_ms()
        self.end_time = None

    def __callback__(self, line):
        self.counter += 1
        for i in range(self.BUFFER_SIZE-1, 0, -1):
            self._sample_times[i]=self._sample_times[i-1]
        else: self._sample_times[0] = ticks_ms()

    @property
    def distance(self): #meters
        irq_state = disable_irq()
        value = (self.counter - 1) * self.STEP
        enable_irq(irq_state)
        return value
    @property
    def duration(self): # seconds
        return ticks_diff(ticks_ms(), self.start_time) * pow(10, -3)

    @property
    def speed(self): #meters/second
        irq_state = disable_irq()
        periods = [ticks_diff(self._sample_times[i], self._sample_times[i+1]) \
                   for i in range(self.BUFFER_SIZE-1)]
        enable_irq(irq_state)
        period = sum([x*y for x,y in zip(self.WEIGHTS, periods)]) * pow(10,-3) #seconds
        speed = self.STEP / period if period > 0 else 0 # meters/second
        return speed * 3.6 # m/s -> km/h
    
    def finish(self):
        self.end_time = ticks_ms()
        self.end_counter = self.counter

    @property
    def rt_data(self): #real time data
        return self.speed, self.distance, self.duration
    
    @property
    def sm_data(self): #summary data
        distance =  (self.end_counter - 1) * self.STEP #meters
        duration =  ticks_diff(self.end_time, self.start_time) * pow(10,-3) #seconds
        speed =  (distance / duration) * 3.6 # m/s -> km/h
        return speed, distance, duration
        
class SpeedController(object):
    IW_LAPSE = const(1000) # increasing speed waiting lapse
    DW_LAPSE = const(300)  # decreasing speed waiting lapse
    
    def __init__(self):
        self.__last_action_time = 0
        self.__lapse = 0
        Pin('SPD+').off()
        Pin('SPD-').off()
        self.speed = Speed()
        #Pin('S/W').on()
        
    def check(self, speed):
        self.__lapse = ticks_diff(ticks_ms(), self.__last_action_time)
        if self.__lapse < self.IW_LAPSE and self.__lapse < self.DW_LAPSE : return False
        if trunc(fabs(speed.delta)*10)/10 < 0.1: return False
        self.speed = speed
        return True

    def execute(self): #leader speed, measured speed
        if self.speed.delta > 0 and self.__lapse > self.IW_LAPSE:
            Pin('SPD+').on() # start increasing speed
            delay(1000)
            Pin('SPD+').off() # stop increasing speed
            self.__last_action_time = ticks_ms()
        elif self.speed.delta < 0  and self.__lapse > self.DW_LAPSE:
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
        self.speed = Speed()
        self.leader = SpeedLeader()
        self.meter = SpeedMeter()
        self.cntrl = SpeedController()
        self.file = open('data.csv', 'w')

    def log(self):
        self.file.write('{0:.1f},{1:.1f},{2:.1f}\n'.format(self.meter.duration, self.speed.ref, self.speed.act))    

    def start(self):
        self.meter.reset()
        self.cntrl.start()
        
    def control(self):
        self.speed.ref = self.leader.speed #get reference speed
        self.speed.act = self.meter.speed  #get actual speed
        #self.log()
        if self.cntrl.check(self.speed): # check speed difference
            self.cntrl.execute() # take action to reduce speed difference

    def slow_down(self):
        self.meter.finish()
        while self.meter.speed > 2.0:
            self.cntrl.slow_down()
        self.file.close()

    def stop(self):
        self.cntrl.stop()
    
