import adafruit_BBIO.GPIO as GPIO




GPIO.setup("P8_10", GPIO.IN)
GPIO.add_event_detect("P9_10", GPIO.RISING)
# GPIO.add_event_dectect("P9_10", GPIO.FALLING)
while True:
	if GPIO.event_detected("P9_10"):
		print 'falling'