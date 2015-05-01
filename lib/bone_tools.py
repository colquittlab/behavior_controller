import Adafruit_BBIO.GPIO as GPIO
import Adafruit_BBIO.PWM as PWM
import time
import execjs
from subprocess import call

import pin_definitions as pindef

## set any enduring parameteres
bouncetime = 250 # bouncetime in ms 





## set all inputs to pullup by default using bonescript (this sucks)
pud = "pullup"
mux = 7
script = "var b = require('bonescript'); "
for pin in pindef.input_definitions.keys():
	script+= "b.pinMode('%s',b.INPUT,%i,'%s'); " % (pin, mux, pud)
command = ["node", "-e", script]
call(command)



## initialize the event buffer
## Create event buffer and create callback function
event_buffer = []
## create function to add to events to buffer
def event_callback(arg):
	event_buffer.append((time.time(), arg))


## initialize all input pins
## activate all inpuyt GPIOS
GPIO.cleanup()
for pin in pindef.input_definitions.keys():
	GPIO.setup(pin, GPIO.IN, GPIO.PUD_UP, 1)
	GPIO.add_event_detect(pin, GPIO.FALLING, callback = event_callback, bouncetime = int(bouncetime))
## initialize all output pins
for pin in pindef.output_definitions.values():
	if type(pin) is str:
		GPIO.setup(pin, GPIO.OUT)
	elif type(pin) is list:
		for pinname in pin:
			GPIO.setup(pinname, GPIO.OUT)



## activate all PWMS
PWM.cleanup()




## function to hit all dersired outputs for a write
def set_output_list(pin_list, value):
        if type(pin_list) is str:
                GPIO.output(pin_list, value)
        elif type(pin_list) is list:
        	for pin in pin_list:
        	        GPIO.output(pin,value)


