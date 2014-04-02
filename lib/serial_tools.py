import os
import serial
from serial.tools import list_ports
from os.path import join
import subprocess

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
    dev = os.listdir('/dev/')
    dev = filter(lambda x: x[0:8] == 'arduino_', dev)
    dev = ['/dev/%s' % d for d in dev]
    return dev

# def find_tty(idVendor, idProduct):
#     """find_tty_usb('067b', '2302') -> '/dev/ttyUSB0'"""
#     # Note: if searching for a lot of pairs, it would be much faster to search
#     # for the enitre lot at once instead of going over all the usb devices
#     # each time.
#     for dnbase in os.listdir('/sys/bus/usb/devices'):
#         dn = join('/sys/bus/usb/devices', dnbase)
#         if not os.path.exists(join(dn, 'idVendor')):
#             continue
#         idv = open(join(dn, 'idVendor')).read().strip()
#         if idv != idVendor:
#             continue
#         idp = open(join(dn, 'idProduct')).read().strip()
#         if idp != idProduct:
#             continue

#         for subdir in os.listdir(dn):
#             if subdir.startswith(dnbase+':'):
#                 for subsubdir in os.listdir(join(dn, subdir)):
#                     if subsubdir.startswith('ttyACM'):
#                         return join('/dev', subsubdir)
#                     elif subsubdir.startswith('ttyUSB'):
#                         return join('/dev', subsubdir)
#                     elif subsubdir.startswith('tty'):
#                         for subsubsubdir in os.listdir(join(dn, subdir,subsubdir)):
#                             if subsubsubdir.startswith('ttyACM'):
#                                 return join('/dev', subsubsubdir)


# def return_list_of_connected_usb_device_ids():
#     data = subprocess.check_output('lsusb')
#     device_ids = []
#     while data.find('ID ') > 0:
#         idx1 = data.find('ID ')+3;
#         idx2 = data[idx1:].find(' ') + idx1
#         devid = data[idx1:idx2]
#         data = data[idx2:]
#         (idvendor,idproduct) = devid.split(':')
#         device_ids.append((idvendor,idproduct))

#         serial_device_ids = []
#         for devid in device_ids:
#             port = find_tty(devid[0], devid[1])
#             if port != None:
#                 serial_device_ids.append((devid[0], devid[1], port))

#     return serial_device_ids




if __name__=='__main__':
    print return_list_of_named_arduinos()