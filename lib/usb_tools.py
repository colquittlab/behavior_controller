import subprocess
import  glob
import  os
import  re
import serial
from serial.tools import list_ports

def list_dev_info():
	device_re = re.compile("Bus\s+(?P<bus>\d+)\s+Device\s+(?P<device>\d+).+ID\s(?P<id>\w+:\w+)\s(?P<tag>.+)$", re.I)
	df = subprocess.check_output("lsusb", shell=True)
	devices = []
	for i in df.split('\n'):
	    if i:
	        info = device_re.match(i)
	        if info:
	            dinfo = info.groupdict()
	            dinfo['device'] = '/dev/bus/usb/%s/%s' % (dinfo.pop('bus'), dinfo.pop('device'))
	            devices.append(dinfo)

	for k, device in enumerate(devices):
		print k, device


def find_usb_tty(vendor_id = None, product_id = None) :
    tty_devs    = []

    for dn in glob.glob('/sys/bus/usb/devices/*') :
        try     :
            vid = int(open(os.path.join(dn, "idVendor" )).read().strip(), 16)
            pid = int(open(os.path.join(dn, "idProduct")).read().strip(), 16)
            if  ((vendor_id is None) or (vid == vendor_id)) and ((product_id is None) or (pid == product_id)) :
                dns = glob.glob(os.path.join(dn, os.path.basename(dn) + "*"))
                for sdn in dns :
                    for fn in glob.glob(os.path.join(sdn, "*")) :
                        if  re.search(r"\/ttyACM[0-9]+$", fn) :
                            #tty_devs.append("/dev" + os.path.basename(fn))
                            tty_devs.append(os.path.join("/dev", os.path.basename(fn)))
                        pass
                    pass
                pass
            pass
        except ( ValueError, TypeError, AttributeError, OSError, IOError ) :
            pass
        pass

    return tty_devs


def return_list_of_usb_serial_ports():
    if os.name == 'nt':
        list_of_ports = []
        # windows
        for i in range(256):
            try:
                s = serial.Serial(i)
                s.close()
                list_of_ports.append('COM' + str(i + 1))
            except serial.SerialException:
                pass
    else:
        # unix
        list_of_ports = [port[0] for port in list_ports.comports()]
    # for port in list_of_ports: print port
    return filter(lambda x: 'ACM' in x, list_of_ports)



if __name__=="__main__":
	print return_list_of_usb_serial_ports()
	list_dev_info()
	print find_usb_tty(vendor_id='0043')