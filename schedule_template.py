""" Template verison of a program to run boc according to a schedule, using the python schedule module"
"""


import behavior_controller as boc
import schedule  
import threading, datetime, time
import random


config_files = ["config_files/pref_test.config",
				"config_files/pref_test.config"]


active_box = None
active_controller = None

def start_box(config_file):
	global active_controller, active_box
	c,b = boc.parse_config(config_file)
	active_controller = c
	active_box = b
	print "about to start box"
	thread = threading.Thread(target = boc.run_box, args = (active_controller, active_box))
	thread.start()
	print "thread done"


def stop_box():	
	print "stopping box"
	global active_controller, active_box
	active_controller.box_state = 'stop'
	active_box.light_off()


def start_task_randomly():
	idx = random.randint(0,len(config_files))
	start_box(config_files[idx])
	pass


def initiate_box():
	c,b = boc.parse_config(config_files[0])
	b.light_off()



# ## tests
# now = datetime.datetime.now()
# starttime = now+datetime.timedelta(seconds=60)
# stoptime =starttime+datetime.timedelta(seconds=60)
# schedule.every().day.at(starttime.strftime('%H:%M')).do(start_task_randomly)
# schedule.every().day.at(stoptime.strftime('%H:%M')).do(stop_box)
# starttime = stoptime+datetime.timedelta(seconds=60)
# stoptime = starttime+datetime.timedelta(seconds=60)
# schedule.every().day.at(starttime.strftime('%H:%M')).do(start_task_randomly)
# schedule.every().day.at(stoptime.strftime('%H:%M')).do(stop_box)

schedule.every().day.at(starttime.strftime('10:00')).do(start_task_randomly)
schedule.every().day.at(stoptime.strftime('12:00')).do(stop_box)
schedule.every().day.at(starttime.strftime('14:00')).do(start_task_randomly)
schedule.every().day.at(stoptime.strftime('16:00')).do(stop_box)

initiate_box()
while True:
	schedule.run_pending()
	time.sleep(1)


# from apscheduler.schedulers.blocking import BlockingScheduler



# sched = BlockingScheduler()

# sched.add_job(start_task1, 'date', run_date=starttime)
# sched.add_job(stop_box, 'date', run_date=stoptime)

