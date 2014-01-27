import serial
from serial.tools import list_ports
import io
import os


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
    return filter(lambda x: 'usb' in x, list_of_ports)


board = return_list_of_usb_serial_ports()
board = board[0]

ser= serial.Serial(board, 115200, parity = serial.PARITY_NONE, xonxoff = True, rtscts = True, dsrdtr = True, timeout = False)
sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser, 1), line_buffering = False)  



while True:
	import ipdb; ipdb.set_trace(); 
	data = sio.read()




# it = util.Iterator(board)
# it.start()
# board.analog[0].enable_reporting()
# board.analog[0].read()

# board.analog[0].enable_reporting = True
