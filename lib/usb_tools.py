import subprocess
import  glob
import  os
import  re
import serial
import alsaaudio as aa
# from serial.tools import list_ports

import serial_tools as st 
import soundout_tools as so 



def return_list_of_boxes():
    list_of_sound_cards = so.list_sound_cards()
    list_of_arduinos = st.return_list_of_named_arduinos()
    boxes_present = []
    for ad in list_of_arduinos:
        if '_' in ad:
            ad_num = ad.split('_')[1]
            for sc in list_of_sound_cards:
                if '_' in sc:
                    sc_num = sc.split('_')[1]
                    if sc_num == ad_num:
                        boxes_present.append(('box_' + ad_num, ad, sc))
    if len(list_of_arduinos)>0 and len(boxes_present)==0:
	boxes_present.append(('box_1',list_of_arduinos[0], aa.cards()[0]))


    return boxes_present                

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

    list_of_ports = filter(lambda x: 'ACM' in x, list_of_ports)
    list_of_ports_and_ids = []
    for port in list_of_ports:
        command = "udevadm info -a -n %s | grep '{serial}' | head -n1" % port
        #command = "udevadm info -a -n %s" % port
        data = os.popen(command)
        data =  data.read()
        data =data.split('"')
        serialnum = data[1]
        list_of_ports_and_ids.append((port, serialnum))
    return list_of_ports_and_ids

def return_list_of_named_arduinos():
    if os.uname()[0]=='Linux': 
        dev = os.listdir('/dev/')
        dev = filter(lambda x: x[0:8] == 'arduino_', dev)
        dev = ['/dev/%s' % d for d in dev]
        return dev
    else:
        return ['arduino_1']

# def list_dev_infWo():
# 	device_re = re.compile("Bus\s+(?P<bus>\d+)\s+Device\s+(?P<device>\d+).+ID\s(?P<id>\w+:\w+)\s(?P<tag>.+)$", re.I)
# 	df = subprocess.check_output("lsusb", shell=True)
# 	devices = []
# 	for i in df.split('\n'):
# 	    if i:
# 	        info = device_re.match(i)
# 	        if info:
# 	            dinfo = info.groupdict()
# 	            dinfo['device'] = '/dev/bus/usb/%s/%s' % (dinfo.pop('bus'), dinfo.pop('device'))
# 	            devices.append(dinfo)

# 	for k, device in enumerate(devices):
# 		print k, device


# def find_usb_tty(vendor_id = None, product_id = None) :
#     tty_devs    = []

#     for dn in glob.glob('/sys/bus/usb/devices/*') :
#         try     :
#             vid = int(open(os.path.join(dn, "idVendor" )).read().strip(), 16)
#             pid = int(open(os.path.join(dn, "idProduct")).read().strip(), 16)
#             if  ((vendor_id is None) or (vid == vendor_id)) and ((product_id is None) or (pid == product_id)) :
#                 dns = glob.glob(os.path.join(dn, os.path.basename(dn) + "*"))
#                 for sdn in dns :
#                     for fn in glob.glob(os.path.join(sdn, "*")) :
#                         if  re.search(r"\/ttyACM[0-9]+$", fn) :
#                             #tty_devs.append("/dev" + os.path.basename(fn))
#                             tty_devs.append(os.path.join("/dev", os.path.basename(fn)))
#                         pass
#                     pass
#                 pass
#             pass
#         except ( ValueError, TypeError, AttributeError, OSError, IOError ) :
#             pass
#         pass

#     return tty_devs


# def return_list_of_usb_serial_ports():
#     if os.name == 'nt':
#         list_of_ports = []
#         # windows
#         for i in range(256):
#             try:
#                 s = serial.Serial(i)
#                 s.close()
#                 list_of_ports.append('COM' + str(i + 1))
#             except serial.SerialException:
#                 pass
#     else:
#         # unix
#         list_of_ports = [port[0] for port in list_ports.comports()]
#     # for port in list_of_ports: print port
#     return filter(lambda x: 'ACM' in x, list_of_ports)



if __name__=="__main__":
    print return_list_of_boxes()
