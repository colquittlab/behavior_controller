""" Template verison of a program to run boc according to a schedule, using the python schedule module"
"""


import behavior_controller as boc
import schedule  
import threading



config_file_1 = "config_files/pref_test.config"
config_file_2 = "config_files/pref_test.config"
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
	active_controller.box_state = 'stop'
	active_box.light_off()


def start_task1():
	start_box(config_file_1)
	pass

def start_task2():
	start_box(config_file_2)
	pass 



import time

start_task1()
time.sleep(30)
stop_box()


# import datetime
# now = datetime.datetime.utcnow()
# starttime = now+datetime.timedelta(seconds=10)
# stoptime = now+datetime.timedelta(seconds=40)


# schedule.every().day().at(starttime.strftime('%H:%M')).do(start_task1)
# schedule.every().day().at(stoptime.strftime('%H:%M')).do(stop_box)


