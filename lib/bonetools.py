import Adafruit_BBIO.GPIO as GPIO
import Adafruit_BBIO.PWM as PWM
import time
import execjs
from subprocess import call


## set all inputs to pullup by default using bonescript
input_pins = ['P8_11']
for pin in input_pins:
	# pin = "P8_11"
	pud = "pullup"
	mux = 7
	script = "var b = require('bonescript'); b.pinMode('%s',b.INPUT,%i,'%s');" % (pin, mux, pud)
	command = 'node -e "%s"' % script
	call(command)


import ipdb; ipdb.set_trace()

GPIO.cleanup()
#PWM.start("P9_14", 50, 1)
GPIO.setup("P8_11", GPIO.IN, GPIO.PUD_UP, 1)
GPIO.setup("P8_12", GPIO.IN, GPIO.PUD_UP, 1)
GPIO.setup("P8_13", GPIO.OUT)
GPIO.setup("P9_12", GPIO.IN, GPIO.PUD_UP, 1)
GPIO.add_event_detect("P8_11", GPIO.FALLING)#,bouncetime = 1)
GPIO.add_event_detect("P9_12", GPIO.FALLING)

node = execjs.get('Node')
node.eval("require('bonescript').getPlatform().bonescript")
# bs = js.compile("""
# 	var b = require('bonescrpt');
# 	function pinMode(pin, pud) {
# 		return b.pinMode(pin, b.INPUT, 7, pud);
# 		}
# 	""")

# bs.call('pinMode', 'P8_11', 'pullup')


# GPIO.add_event_dectect("P9_10", GPIO.FALLINGPIO.add_event_detect("P8_11", GPIO.FALLING, bouncetime = 100000)G,bouncetime = 100)
import ipdb; ipdb.set_trace()
count = 0
while True:
	if GPIO.event_detected("P8_11"):
		count += 1
		print time.time(), count, 'falling'
	if GPIO.event_detected("P9_12"):
		count += 1
		print time.time(), count, 'falling'

