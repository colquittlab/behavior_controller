import Adafruit_BBIO.GPIO as GPIO
import Adafruit_BBIO.PWM as PWM
import time
import execjs
from subprocess import call

import pin_definitions as pindef


## set all inputs to pullup by default using bonescript (this sucks)
for pin in pindef.input_definitions.keys():
	# pin = "P8_11"
	pud = "pullup"
	mux = 7
	script = "var b = require('bonescript'); b.pinMode('%s',b.INPUT,%i,'%s');" % (pin, mux, pud)
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
	GPIO.add_event_detect(pin, GPIO.FALLING, callback = event_callback, bouncetime = 250)
## initialize all output pins
for pin in pindef.output_definitions.values():
	GPIO.setup(pin, GPIO.OUT)


## activate all PWMS
PWM.cleanup()
