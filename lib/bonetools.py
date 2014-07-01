import Adafruit_BBIO.GPIO as GPIO
import Adafruit_BBIO.PWM as PWM
import time
import execjs
from subprocess import call


## set all inputs to pullup by default using bonescript (this sucks)
input_pins = ['P8_11', 'P8_12']
for pin in input_pins:
	# pin = "P8_11"
	pud = "pullup"
	mux = 7
	script = "var b = require('bonescript'); b.pinMode('%s',b.INPUT,%i,'%s');" % (pin, mux, pud)
	command = ["node", "-e", script]
	call(command)



GPIO.cleanup()
for pin in input_pins:
	GPIO.setup(pin, GPIO.IN, GPIO.PUD_UP, 1)
	GPIO.add_event_detect("P8_11", GPIO.FALLING, bouncetime = 100000)





count = 0
while True:
	if GPIO.event_detected("P8_11"):
		count += 1
		print time.time(), count, 'falling'
	if GPIO.event_detected("P9_12"):
		count += 1
		print time.time(), count, 'falling'

