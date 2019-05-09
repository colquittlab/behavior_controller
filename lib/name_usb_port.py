import sys
from subprocess import call, Popen
import os

udev_rules_dir = '/etc/udev/rules.d/'
udev_rules_name = 'audio_usb_portnames.rules'
udev_rules_num = 30
udev_rules_fname = '%d-%s' % (udev_rules_num, udev_rules_name)
udev_rules_fpath = os.path.join(udev_rules_dir,udev_rules_fname)


def parse_udev_file(fname):
	device_dict = {}
	f = open(udev_rules_fpath,'r')
	for line in f:
		if line[0:7]=='DEVPATH':
			tolkens = line.split('"')
			syspath = tolkens[1]
			syspath=syspath[:-2]
			portnum = int(tolkens[3][9:])
			device_dict[syspath] = portnum
	f.close()
	return device_dict
def write_udev_file(device_dict):
	f = open(udev_rules_fpath, 'w')
	f.write('SUBSYSTEM!="sound", GOTO="my_usb_audio_end"\n')
	f.write('ACTION!="add", GOTO="my_usb_audio_end"\n')
	for key in device_dict.keys():
		f.write('DEVPATH=="%s/*", ATTR{id}="usbaudio_%d"\n' % (key, device_dict[key]))
	f.write('LABEL="my_usb_audio_end"\n')
	f.close()
	pass


if __name__ == "__main__":
	if len(sys.argv) > 1:
		search_term = sys.argv[1]
	else:
		search_term = "audio"
	print "Search Term: %s" % search_term

	# get usb devices
	lines = []
	for line in os.popen('lsusb'):
		if search_term.lower() in line.lower():
			lines.append(line.strip('\n'))
	if len(lines) is 0:
		Exception('No device found for %s' % search_term)
	elif len(lines) is 1:
		print 'Device found for %s:\n %s' % (search_term, lines[0])
	else:
		print 'Multiple Devices found for %s.  Using the first:\n %s' % (search_term, lines[0]) 
    
    # generate sym link path and query system path
	bus = lines[0].split()[1].strip(':')
	dev = lines[0].split()[3].strip(':')
	sympath='/dev/bus/usb/%s/%s' % (bus,dev)
	print 'device sym link path: %s' % sympath
	syspath = os.popen('sudo udevadm info --name=%s --query=path' % sympath).read().strip('\n')
	print 'usb port system path: %s\n' % syspath

	# read from udev file if it exists
	if os.path.isfile(udev_rules_fpath):
		device_dict = parse_udev_file(udev_rules_fpath)
		if syspath in device_dict.keys():
			print 'This port is already named as usbaudio_port%d\n' % device_dict[syspath]
			iresult = raw_input('Rename? ["y" or any other key to exit] ')
			if str(iresult).lower() != 'y':
				sys.exit()
	else:
		iresult = raw_input('No udev file found at %s    Create file? ["y" or any key to exit] ' % udev_rules_fpath)
		if str(iresult).lower()=='y':
			device_dict = {}
		else:
			sys.exit()

	portnumassigned = False
	while not portnumassigned:
		iresult = raw_input('Enter audioport number for usb audio port %s  ' % syspath)
		try:
			port_number = int(iresult)
			if port_number in device_dict.values():
				if syspath in device_dict.keys() and device_dict[syspath] == port_number:
					portnumassigned =  True
				else:
					iresult = raw_input('port %d is already assigned. Enter "o" overwrite, "n" to enter a new port assignment or "q" to quit ')
					if str(iresult).lower()=='o':
						device_dict.pop(device_dict.keys()[device_dict.values().index(port_number)])
						device_dict[syspath]=port_number
						portnumassigned=True
					elif str(iresult).lower()=='q':
						sys.exit()
					else:
						pass
			else:
				device_dict[syspath] = port_number
				portnumassigned = True
		except:
			if str(iresult).lower()=='q':
				sys.exit()
			print '%s is not an integer. Please enter a new number\n' % iresult



	if len(set(device_dict.keys())) != len(device_dict):
		('Syspath assigned multiple ports')
	if len(set(device_dict.values())) != len(device_dict):
		Exception('Port assigned to multiple syspaths')

	write_udev_file(device_dict)
	os.popen('udevadm control --reload-rules')









	
