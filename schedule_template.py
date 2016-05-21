""" Template verison of a program to run boc according to a schedule, using the python schedule module"
"""


import behavior_controller as boc
import schedule  
import threading, datetime, time
import random
from numbers import Number



config_files = ["config_files/bsp_tbase.config", 'bsp_tnull.config']

stimset_pool = ['bsp_v2_6p5_ss_stimset','bsp_v2_8p5_ss_stimset','bsp_v2_10p5_ss_stimset','bsp_v2_zebrasong_stimset', 'bsp_v3_silent_stimset', 'bsp_v3_whitenoise_stimset']

config_files_by_session = []


active_box = None
active_controller = None

def start_box(config_file, randomize_stimsets=False):
	global active_controller, active_box, config_files, stimset_pool
	if isinstance(config_file, Number):
		config_file = config_files[config_file]
	else:
		pass
	c,b = boc.parse_config(config_file)
	if randomize_stimsets:
		c.stimset_names = []
		stimset_idxs = range(0,len(stimset_pool))
		for k in range(0,2):
			idx = random.sample(stimset_idxs,1)[0]
			stimset_idxs.remove(idx)
			c.stimset_names.append(stimset_pool[idx])
		c.load_stimsets()
	active_controller = c
	active_box = b
	print "about to start box"
	thread = threading.Thread(target = boc.run_box, args = (active_controller, active_box))
	thread.start()
	print "thread done"


def stop_box():	
	try:
		print "stopping box"
		global active_controller, active_box
		active_controller.box_state = 'stop'
		active_box.light_off()
	except:
		pass


def start_task_randomly():
	idx = random.randint(0,len(config_files))
	start_box(config_files[idx])
	pass


def initiate_box():
	c,b = boc.parse_config(config_files[0])
	b.light_off()


def generate_sessions_for_day(n_sessions=5):
	global config_files_by_session
	config_files_by_session=[]
	# pick sessions randomly from config files
	for k in range(1,n_sessions):
		idx = random.randint(0,len(config_files)-1)
		config_files_by_session.append(config_files[idx])
	# 
	pass

def start_session(session_num=0):
	global config_files_by_session
	start_box(config_files_by_session[session_num])
	pass

def printme(session_num=0):
	global config_files_by_session
	print config_files_by_session[session_num]




# ## tests
# now = datetime.datetime.now()
# starttime = now+datetime.timedelta(seconds=60)
# stoptime =starttime+datetime.timedelta(seconds=60)
# schedule.every().day.at(starttime.strftime('%H:%M')).do(generate_sessions_for_day)
# starttime = starttime+datetime.timedelta(seconds=60)
# schedule.every().day.at(starttime.strftime('%H:%M')).do(printme,0)
# starttime = starttime+datetime.timedelta(seconds=60)
# schedule.every().day.at(starttime.strftime('%H:%M')).do(printme,1)
# schedule.every().day.at(starttime.strftime('%H:%M')).do(start_task_randomly)
# schedule.every().day.at(stoptime.strftime('%H:%M')).do(stop_box)
# starttime = stoptime+datetime.timedelta(seconds=60)
# stoptime = starttime+datetime.timedelta(seconds=60)
# schedule.every().day.at(starttime.strftime('%H:%M')).do(start_task_randomly)
# schedule.every().day.at(stoptime.strftime('%H:%M')).do(stop_box)



schedule.every().day.at('00:01').do(generate_sessions_for_day)
schedule.every().day.at('09:00').do(start_box,0,randomize_stimsets=True)
schedule.every().day.at('10:00').do(stop_box)
schedule.every().day.at('10:01').do(start_box,'bsp_tnull')
schedule.every().day.at('10:02').do(eval,'active_box.light_off()')

schedule.every().day.at('10:59').do(stop_box)
schedule.every().day.at('11:00').do(start_box,0,randomize_stimsets=True)
schedule.every().day.at('12:00').do(stop_box)
schedule.every().day.at('12:01').do(start_box,'bsp_tnull')
schedule.every().day.at('12:02').do(eval,'active_box.light_off()')

schedule.every().day.at('12:59').do(stop_box)
schedule.every().day.at('13:00').do(start_box,0,randomize_stimsets=True)
schedule.every().day.at('14:00').do(stop_box)
schedule.every().day.at('14:01').do(start_box,'bsp_tnull')
schedule.every().day.at('14:02').do(eval,'active_box.light_off()')


schedule.every().day.at('14:59').do(stop_box)
schedule.every().day.at('15:00').do(start_box,0,randomize_stimsets=True)
schedule.every().day.at('16:00').do(stop_box)
schedule.every().day.at('16:01').do(start_box,'bsp_tnull')
schedule.every().day.at('16:02').do(eval,'active_box.light_off()')

schedule.every().day.at('16:59').do(stop_box)
schedule.every().day.at('17:00').do(start_box,0,randomize_stimsets=True)
schedule.every().day.at('18:00').do(stop_box)
schedule.every().day.at('18:01').do(start_box,'bsp_tnull')
schedule.every().day.at('18:02').do(eval,'active_box.light_off()')




initiate_box()
while True:
	schedule.run_pending()
	time.sleep(1)


# from apscheduler.schedulers.blocking import BlockingScheduler



# sched = BlockingScheduler()

# sched.add_job(start_task1, 'date', run_date=starttime)
# sched.add_job(stop_box, 'date', run_date=stoptime)

