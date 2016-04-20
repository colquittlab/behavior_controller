""" Template verison of a program to run boc according to a schedule, using the python schedule module"
"""


import behavior_controller as boc
import schedule  
import threading



config_file_1 = "config/pref_test.config"
config_file_2 = "config/pref_test.config"
active_box = None
active_controller = None

def start_box(config_file):
	global active_controller, active_box
	c,b = boc.parse_config(config_file)
	active_controller = c
	active_box = b
	threading.Thread(target = boc.run_box, args = (active_controller, active_box))



def stop_box():
	global active_controller, active_box
	controller.box_state = 'stop'
	box.light_off()




