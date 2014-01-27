import serial
import io
import time
import os
import shutil
ser = serial.Serial('/dev/cu.usbmodemfa132', 115200, parity = serial.PARITY_NONE, xonxoff = True, rtscts = True, dsrdtr = True, timeout = 2)
sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser, 1), line_buffering = False)

def send_command_to_microcontroller(serial_object, command):


	for x in command:
		sio.write(unicode(x))
		sio.flush()
		time.sleep(0.005)


	#ser.write(command)
	# command = unicode(command)


	ser.close() 

def send_file_to_microcontroller(serial_object, fname):
	f = open(fname)
	send_command_to_microcontroller(serial_object, f.read())
	f.close()

def delploy_file_as_startup_script(fname):
	shutil.copy(fname, '/Volumes/MBED/STARTUP.TXT')



if __name__ == '__main__':
	delploy_file_as_startup_script('sandbox.mk')
	#send_file_to_microcontroller(ser, 'sandbox.mk')


