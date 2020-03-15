from pyb import Pin

Pin.dict({ 'SPD' : Pin.cpu.A0, # speed input
           'S/W' : Pin.cpu.A1, # enable speed control SPD+ and SPD-
           'SPD+': Pin.cpu.A4, # increase speed
           'SPD-': Pin.cpu.A5, # decrease speed
           'INC+': Pin.cpu.A3, # increase tilt
           'INC-': Pin.cpu.A2, # decrease tilt
           'rSPD': Pin.cpu.B0, # reference speed
           'rINC': Pin.cpu.B1, # reference tilt
           'lBlue':Pin.cpu.C3, # blue led
           'lGreen':Pin.cpu.C2, # green led
           'lRed':Pin.cpu.C1, # red led           
           'Buzzer':Pin.cpu.C0, # buzzer
           'ON/OFF': Pin.cpu.B13 # Start/Stop Button
})

Pin('SPD').init(Pin.IN)
Pin('S/W').init(Pin.OUT_PP, Pin.PULL_UP)
Pin('SPD+').init(Pin.OUT_PP, Pin.PULL_DOWN)
Pin('SPD-').init(Pin.OUT_PP, Pin.PULL_DOWN)
Pin('INC+').init(Pin.OUT_PP)
Pin('INC-').init(Pin.OUT_PP)
Pin('lBlue').init(Pin.OUT_PP)
Pin('lGreen').init(Pin.OUT_PP)
Pin('lRed').init(Pin.OUT_PP)
Pin('Buzzer').init(Pin.OUT_OD)
Pin('rSPD').init(Pin.IN, Pin.PULL_UP)
Pin('rINC').init(Pin.IN, Pin.PULL_UP)
Pin('ON/OFF').init(Pin.IN)

