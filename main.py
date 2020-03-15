from pyb import Pin, wfi, delay, hard_reset
from time import sleep

import micropython
micropython.alloc_emergency_exception_buf(100)

import config
Pin('Buzzer').init(Pin.OUT_OD)
Pin('Buzzer').high() # silent buzzer

from board import Board
from mcu import MCU
from speed import SpeedManager
from slope import SlopeManager

mcu = MCU() # blink yellow 
spd_mngr = SpeedManager()
slp_mngr = SlopeManager()
uboard = Board(spd_mngr, slp_mngr) #user board

while True:
    #making sure speed and slope leaders go down on red light
    mcu.yellow();uboard.start() # yellow color
    
    while uboard.isReady() is not True: delay(1000); wfi()
    else: mcu.green(); uboard.setReady() #green light and beep: it's safe to get onboard

    # waiting for start/stop button to be pushed
    while uboard.isOn() is not True: delay(1000); wfi()
    else: mcu.blue(); uboard.setOn() #blue light and three beeps to state to getting started

    # action is about to start    
    spd_mngr.start()
    #walking: control loop
    while uboard.isOn(): # control loop remain until start/stop button is pushed
        spd_mngr.control()
        slp_mngr.control()
    else: #stop procedure
        mcu.red()
        uboard.stopping() # red light and three beeps
        spd_mngr.slow_down() # reduce speed until 2.0 km/h
        slp_mngr.get_down()  # get down slope to horizontal level
        spd_mngr.stop()      # zero speed
        
    mcu.green();uboard.stopped() # green light and three long beeps
    # getting down from machine    
    sleep(30) # before starting new loop 30 seconds wait

# just in case
mcu.random()
spd_mngr.stop()
hard_reset()
    

    
