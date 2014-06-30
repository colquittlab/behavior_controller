import Adafruit_BBIO.GPIO as GPIO
import Adafruit_BBIO.PWM as PWM
import time

GPIO.cleanup()
#PWM.start("P9_14", 50, 1)
GPIO.setup("P8_30", GPIO.IN)
GPIO.setup("P8_12", GPIO.IN)
GPIO.setup("P8_13", GPIO.OUT)
GPIO.setup("P9_12", GPIO.IN)
GPIO.add_event_detect("P8_30", GPIO.FALLING)#,bouncetime = 1)
GPIO.add_event_detect("P9_12", GPIO.FALLING)

# GPIO.add_event_dectect("P9_10", GPIO.FALLINGPIO.add_event_detect("P8_11", GPIO.FALLING, bouncetime = 100000)G,bouncetime = 100)
# import ipdb; ipdb.set_trace()
count = 0
while True:
	if GPIO.event_detected("P8_30"):
		count += 1
		print time.time(), count, 'falling'
	if GPIO.event_detected("P9_12"):
		count += 1
		print time.time(), count, 'falling'
