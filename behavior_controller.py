#! /usr/bin/env python

import scipy as sp
import numpy as np
from scipy import io as spio
import os
import serial
from serial.tools import list_ports
import time
import datetime
import io
import json
import ConfigParser
import sys
import Queue
import warnings
import pdb
import lib.soundout_tools as so
import lib.serial_tools as st
import lib.arduino_tools as at
import lib.usb_tools as ut
import lib.audiorecording_tools as ar
import loop_iterations as loop
import trial_generators as trial
import lib.pin_definitions as pindef
try:
    import lib.bone_tools as bt
except Exception as e:
    bt = None
    warnings.warn('lib.bonetools import failed.  beaglebone functionality disabled. \n execute \npython import lib/bonetools.py for details.')
try:
    import lib.video_tracking as vt
except:
    warnings.warn('lib.videotracking import failed.  videotracking functionality disabled',UserWarning)
    vt = None
try:
    import lib.videoplayback_tools as vpt
except:
    warnings.warn('lib.videoplayback_tools import failed.  videoplayback functionality disabled',UserWarning)
    vpt = None

# from pyfirmata import Arduino, util
baud_rate = 19200
time_tollerance = 200e-3
debug = True
beep = False
## Settings
mode_definitions = loop.iterations.keys()
default_stimuli_dir = '/data/stimuli/'
default_data_dir = '/data/behavior/'

class GracefulKiller:
    # http://stackoverflow.com/questions/18499497/how-to-process-sigterm-signal-gracefully/31464349#31464349
    kill_now = False
    def __init__(self):
      signal.signal(signal.SIGINT, self.exit_gracefully)
      signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self,signum, frame):
      self.kill_now = True

class BehaviorController(object):
    def __init__(self):
        self.birdname = None
        # save the date and time
        self.initial_date = datetime.datetime.now()

        # file names ext
        self.base_filename = None
        self.has_run = False
        self.log_fid = None
        self.trial_fid = None
        self.errlog_fid = None

        self.config_file_contents = None

        # initialize the state variables
        self.task_state = None
        self.box_state = 'stop'

        # initialize trial variables
        self.event_count = 0
        self.trial_block = []
        self.current_trial = None
        self.completed_trials = []

        # initialize tallies
        self.reward_count = 0
        self.rewards_per_session = {}
        self.timeout_count = 0
        self.event_time = 0

        # initialize the stimset holders
        self.stimsets = []
        self.stimset_names = []

        # initialize the task parameters
        self.params = {}
        self.params['mode'] = None
        self.expected_responses = ['response_a', 'response_b']

        self.params['data_dir'] = default_data_dir
        self.params['stimuli_dir'] = default_stimuli_dir

        # initialize the task parameters
        self.params['timeout_period'] = 60; # timeout (punishment) time in seconds
        self.params['max_trial_length'] = 5; # maximum trial time in seconds
        self.params['feed_time'] = 5;
        self.params['timeout_light'] = True
        self.params['minimum_response_time'] = 0.6

        self.params['withold_response'] = False
        self.params['warn_feeder_off'] = False

        # initializethe trial variables
        self.params['trial_generator'] = 'standard'

        # trial
        self.params['stimset_occurance'] = [0.5, 0.5]
        self.params['probe_occurance'] = 0
        self.params['laser_occurance'] = 0
        self.params['pulse_width'] = 50
        self.params['pulse_period'] = 100
        self.params['allowed_songs_per_session'] = 10
    
        # parameters for playback mode
        self.params['delay_time'] = 5
        self.params['isi_distribution'] = 'exponential'
        self.params['isi_parameter'] = 10
        self.params['set_times'] = 0
        self.params['trigger_window'] = 0
        self.params['min_trigger_duration'] = 0
        self.params['max_trigger_entropy'] = 0
        self.params['min_trigger_power'] = 0
        self.params['max_stim_limit'] = 0
        
        
        # stimset occurance
        self.Aocc = 0.5
        self.Bocc = 1.0 - self.Aocc

        # generic playback files
        self.white_noise = 'sounds/wn.wav'



    def set_bird_name(self, birdname):
        if not self.has_run:
            self.birdname = birdname
        self.generate_file_name()

    def generate_file_name(self):
        if self.base_filename is not None:
            return self.base_filename
        basename = '%s_%04d%02d%02d' %(self.birdname,self.initial_date.year,self.initial_date.month,self.initial_date.day)
        idx = 0
        while os.path.exists('%s%s_%d.log'%(self.params['data_dir'], basename,idx)):
            idx += 1
        name = '%s_%d'%(basename,idx)
        self.base_filename = name
        pass

    def ready_to_run(self):
        if self.birdname is None:
            return (False, 'birdname not set')
        if self.base_filename is None:
            return (False, 'filename not set')
        if len(self.stimsets) < 2:
            return (False, 'stimsets not loaded')
        if self.mode is None:
            return (False, 'mode not set')
        return (True, 'ready_to_run')

    @property
    def n_trials(self):
        return len(self.completed_trials)

    def load_stimsets(self):
        #if len(self.stimset_names) < 2:
        #    raise Exception('Error: less than 2 stimset names set')
        self.stimsets = []
        for k,name in enumerate(self.stimset_names):
            self.params['stimset_%d' % k] = name
            self.stimsets.append(load_and_verify_stimset(self.params['stimuli_dir'], name))
        pass

    def list_stimuli(self, stimset_idxs = None):
        if stimset_idxs == None:
            stimset_idxs = range(len(self.stimsets))
        stimuli = []
        for stimset_idx in stimset_idxs:
            stimset = self.stimsets[stimset_idx]
            stimuli.extend([(stimset_idx, kstim, stim['name']) for kstim,stim in enumerate(stimset['stims'])])
        return stimuli

    def que_next_trial(self):
        print self.current_trial
        if self.current_trial != None:
            self.store_current_trial()
        if len(self.trial_block) < 1:
            self.trial_block = trial.generators[self.params['trial_generator']](self)
        self.current_trial = self.trial_block.pop(0)
        print self.current_trial
        pass

    def store_current_trial(self):
        self.completed_trials.append(self.current_trial)
        self.save_trial_to_file(self.current_trial)
        self.current_trial = None
        pass

    def return_log_fid(self):
        if self.log_fid == None:
#            self.log_fid = open('%s%s.log'% (self.params['data_dir'],self.base_filename), 'w')
            self.log_fid = open('%s%s.log'% (self.params['data_dir'],self.base_filename), 'a')
        return self.log_fid

    def return_events_fid(self):
        if self.trial_fid == None:
#            self.trial_fid = open('%s%s.trial'% (self.params['data_dir'],self.base_filename), 'w')
            self.trial_fid = open('%s%s.trial'% (self.params['data_dir'],self.base_filename), 'a')
        return self.trial_fid

    def return_errlog_fid(self):
        if self.errlog_fid == None:
#            self.trial_fid = open('%s%s.trial'% (self.params['data_dir'],self.base_filename), 'w')
            self.errlog_fid = open('%s%s.errlog'% (self.params['data_dir'],self.base_filename), 'a')
        return self.errlog_fid


    def save_config_file(self):
        config_fname = '%s%s.config'% (self.params['data_dir'],self.base_filename)
        if self.config_file_contents is not None:
            config_fid = open(config_fname, 'w')
            config_fid.write(self.config_file_contents)
        else:
            config = ConfigParser.ConfigParser()
            config.add_section('run_params')
            for key in self.params.keys():
                config.set('run_params', key, self.params[key])
            config.add_section('record_params')
            for key in self.recorder.params.keys():
                config.set('record_params', key, self.recorder.params[key])
        pass

    def save_events_to_log_file(self,  events_since_last):
        fid = self.return_log_fid()
        for event in events_since_last:
            if event[1] == 'audio_threshold_crossing':
                continue
            # tally counts from events
            self.event_count += 1
            if event[1] == "reward_start":
                self.reward_count += 1
            if event[1] == "timeout_start":
                self.timeout_count += 1

            fid.write("%d:%s\n"%(self.event_count, str(event)))
            if debug:
                #print "%s: %d %s"%(box.box_name, self.event_count, str(event))
                print "%s events:%d, trials:%d, rewards:%d, tos:%d, %s"%(self.box.box_name, self.event_count, self.n_trials, self.reward_count, self.timeout_count, str(event)) #GK
                if beep:
                    so.beep()
        fid.flush()
        pass

    def save_trial_to_file(self, trial):
        trial['mode'] = self.params['mode']
        fid = self.return_events_fid()
        fid.write('%s\n' % json.dumps(trial))
        fid.flush()
        pass

    def write_error(self, e):
        errlog_fid = self.return_errlog_fid()
        errlog_fid.write(time.ctime() + " ")
        tb.print_exc(file=errlog_fid)

    def calculate_performance_statistics(self, n_trials_back = None):
        stats = {}
        stats['by_stimset'] = []
        if n_trials_back != None:
            if len(self.completed_trials) > n_trials_back:
                relevant_trials = self.completed_trials[len(self.completed_trials) - n_trials_back-1:]
            else:
                relevant_trials = self.completed_trials
        else:
            relevant_trials = self.completed_trials
        # initialize recording dictionaries
        for stimset_idx in range(0, len(self.stimsets)):
            stats['by_stimset'].append({})
            stats['by_stimset'][stimset_idx]['n_correct'] = 0
            stats['by_stimset'][stimset_idx]['n_incorrect'] = 0
            stats['by_stimset'][stimset_idx]['n_haulted'] = 0
            stats['by_stimset'][stimset_idx]['n_noresponse'] = 0
            stats['by_stimset'][stimset_idx]['n_occurances'] = 0
        # count events in trials
        for trial in relevant_trials:
            if 'stimset_idx' in trial.keys():
                stats['by_stimset'][trial['stimset_idx']]['n_occurances'] += 1
                if 'result' in trial.keys():
                    if trial['result'] == 'correct':
                        stats['by_stimset'][trial['stimset_idx']]['n_correct'] += 1
                    elif trial['result'] == 'incorrect':
                        stats['by_stimset'][trial['stimset_idx']]['n_incorrect'] += 1
                    elif trial['result'] == 'haulted':
                        stats['by_stimset'][trial['stimset_idx']]['n_haulted'] += 1
                    elif trial['result'] == 'no_response':
                        stats['by_stimset'][trial['stimset_idx']]['n_noresponse'] += 1

        stats['nchoices'] = 0
        for stimset_idx in range(0, len(self.stimsets)):
            stats['nchoices'] += stats['by_stimset'][stimset_idx]['n_occurances']
        # calculate statisics for each stimset
        for stimset_idx in range(0, len(self.stimsets)):
            if (stats['by_stimset'][stimset_idx]['n_correct'] + stats['by_stimset'][stimset_idx]['n_incorrect']) == 0:
                stats['by_stimset'][stimset_idx]['p_correct'] = 0
            else:
                stats['by_stimset'][stimset_idx]['p_correct'] = float(stats['by_stimset'][stimset_idx]['n_correct']) / (stats['by_stimset'][stimset_idx]['n_correct'] + stats['by_stimset'][stimset_idx]['n_incorrect'])
            if stats['nchoices'] > 0:
                stats['by_stimset'][stimset_idx]['p_occurance'] = float(stats['by_stimset'][stimset_idx]['n_occurances']) / stats['nchoices']
            else:
                stats['by_stimset'][stimset_idx]['p_occurance'] = 0.5
        return stats


class BehaviorBox(object):
    """this object holds the present state of the behavior Arduino
    and contains the methods to change the pins of the box"""
    def __init__(self):
        #
        self.birdname = None
        self.stimuli_dir = None
        self.serial_buffer = ""
        self.box_name = None
        self.sc_out_idx = None
        self.pcm_out = None
        self.so_workers = []
        self.pulse_state = 0
        self.force_feed_up = False
        self.video_event_queue = None
        self.audio_event_queue = None
        self.audio_control_queue = None
        self.video_control_queue = None
        self.video_tracking_process = None
        self.video_capture_process = None
        self.video_playback_object = None
        self.box_zero_time = 0
        self.last_sync_time = 0
        self.sync_period = 60*30
        self.serial_port = None
        self.serial_device_id = None
        self.serial_c = None
        self.serial_io = None
        self.arduino_model = "uno"
        self.trigger_value = True
        self.recorder = None #ar.AudioRecord()
        self.media_outdir = None
        self.last_stim = 0
        # bt.PWM.start(pindef.output_definitions['pwm_pin'], 15, 1000)

    def ready_to_run(self):
        if not self.serial_status:
            return (False, 'serial not connected')
        if self.sc_idx is None:
            return (False, 'soundcard not set')
        return (True, 'ready_to_run')

    @property
    def serial_status(self):
        if self.serial_c != None:
            return self.sync()
        else: return False

    def query_events(self, timeout = 0):
        events_since_last = []

        if bt is not None: # if bonetools is active, query beaglebone events
            while len(bt.event_buffer) > 0:
                event = bt.event_buffer.pop(0)
                event_out = [event[0]]
                event_out.extend(pindef.input_definitions[event[1]])
                events_since_last.append(tuple(event_out))

        if self.serial_c is not None: # if arduino connection has been activated, query arduino events
            arduino_events = self.query_arduino_events()
            events_since_last.extend(arduino_events)

        # if video tracking is active, query any videotracking events
        if self.video_event_queue is not None:
            while not self.video_event_queue.empty():
                try:
                    event = self.video_event_queue.get_nowait()
                    events_since_last.append(event)
                except Queue.Empty:
                    pass
            pass

        if self.audio_event_queue is not None:
            while not self.audio_event_queue.empty():
                try:
                    event = self.audio_event_queue.get_nowait()
                    events_since_last.append(event)
                except Queue.Empty:
                    pass

        return events_since_last

    def select_serial_port(self, port = None):
        if port is not None:
            self.serial_port = port;
        else:
            list_of_ports = st.return_list_of_usb_serial_ports()
            print 'Select desired port from list below:'
            for k,port in enumerate(list_of_ports):
                print '[%d] port: %s serial# %s' % (k,port[0], port[1])
            # x = input('Enter Number: ')
            x = 0
            self.serial_port = list_of_ports[x][0]
            self.serial_device_id = list_of_ports[x][1]
        result = self.connect_to_serial_port()
        return result

    def connect_to_serial_port(self):
        try:
            self.serial_c = serial.Serial(self.serial_port, baud_rate, parity = serial.PARITY_NONE, bytesize = serial.EIGHTBITS, stopbits = serial.STOPBITS_ONE, xonxoff = False, rtscts = False, timeout = False)
            self.serial_c.setDTR(False)
            self.serial_c.flushInput()
            self.serial_c.flushOutput()
            self.serial_c.setDTR(True)
            self.serial_io = io.TextIOWrapper(io.BufferedRWPair(self.serial_c, self.serial_c, 20), line_buffering = False, newline='\r')
            time.sleep(2)
            return self.sync()
        except:
            self.reload_arduino_firmware()
            return self.connect_to_serial_port()

    def reload_arduino_firmware(self):
        at.build_and_upload(self.serial_port, arduino_model = self.arduino_model)

    def sync(self):

        send_time = self.current_time
        self.write_command('<sync>')
        events = []
        count = 0
        events = self.query_arduino_events(timeout = 2)
        sync_time = None
        for event in events:
            if len(event) > 1 and event[1]=='sync':
                sync_time = float(event[0])
        if sync_time != None:
            self.box_zero_time = send_time - float(sync_time)/1000
            self.last_sync_time = self.current_time;
            return True
        else:
            raise(st.SerialError('Sync not successful'))
        return True

    def query_arduino_events(self, timeout = 0):
        events_since_last = []
        try:
            if timeout != self.serial_c.timeout:
                self.serial_c.timeout = timeout
            # read any new input into the buffer
            self.serial_buffer += self.serial_io.read()
        except KeyboardInterrupt:
            raise
        except:
            raise st.SerialError('serial connection lost')

        # read any exigent events out of the serial buffer and add them to events_since_last
        while True:
            idx1 = self.serial_buffer.find('<')
            idx2 = self.serial_buffer[idx1:].find('>')
            if idx1 > -1 and idx2 > -1:
                idx2 = idx2 + idx1 + 1
                line = self.serial_buffer[idx1:idx2]
                event = self.parse_event_from_line(line)
                if event != None:
                    events_since_last.append(event)
                self.serial_buffer = self.serial_buffer[idx2:]
            else:
                return events_since_last
    def parse_event_from_line(self,line):
        line = line.strip('\n')
        line = line.strip('\r')

        idx1 = line.find('<')
        idx2 = line.find('>')
        if idx1 > -1 and idx2 > -1:
        # if len(line)>0 and line[0]=='<' and line[-1]=='>': # this needs better care
            line_parts = line[idx1+1:idx2].split('-')
            if len(line_parts) is 3:
                box_time = float(line_parts[0])
                box_time = float(box_time)/1000 + self.box_zero_time
                port = int(line_parts[1])
                state = int(line_parts[2])
            elif line_parts[1].lower() == "sync":
                return (line_parts[0],line_parts[1],self.current_time)
            else: return None
        else: return None
        if port in pindef.input_definitions.keys():
            if state == self.trigger_value:
                event = [box_time] + pindef.input_definitions[port]
            else: return None
        else: return None
        return tuple(event)


    @property
    def current_time(self):
        return time.time()

    def activate_box(self, box_name):
        list_of_boxes = ut.return_list_of_boxes()

        box_data = list_of_boxes[0]
        self.select_sound_card(box_data[2])
        self.box_name = box_name

    def return_list_of_sound_cards(self):
        return so.list_sound_cards()

    def select_sound_card(self, cardname = None, playback=False):
        list_of_cards = self.return_list_of_sound_cards()
        if cardname == None:
            print 'Select desired card from list below:'
            for k,card in enumerate(list_of_cards):
                print '[%d] %s' % (k,card)
            idx = input('Enter Number: ')
            #idx = len(list_of_cards)-1
        elif type(cardname)==int:
            idx = cardname
        else:
            idx = list_of_cards.index(cardname)
            
        if not playback:
            self.sc_idx = idx
        else:
            
            self.sc_out_idx = idx
            self.pcm_out = list_of_cards[idx]
        print idx

    def feeder_on(self):
        # bt.set_output_list(pindef.output_definitions['feeder_port'], 1)
        # try:
        #     bt.PWM.set_duty_cycle(pindef.output_definitions['pwm_pin'], 85)
        # except:
        #     print 'unable to set pwm port'
        pass
    def feeder_off(self, do_warning=False):
     #    if do_warning:
     #        self.beep_warning()
     #        time.sleep(1)
     #        pass
     #    bt.set_output_list(pindef.output_definitions['feeder_port'], 0)

     #    try:
            # bt.PWM.set_duty_cycle(pindef.output_definitions['pwm_pin'],15)
     #    except:
     #        print 'unable to set pwm port'
     pass

    def light_on(self):
        # bt.set_output_list(pindef.output_definitions['light_port'], 0)
        pass
    def light_off(self):
        # bt.set_output_list(pindef.output_definitions['light_port'], 1)
        pass
    def pulse_on(self, freq=100, duty=50):
        # bt.PWM.start(pindef.output_definitions['laser_port'], duty, freq, 1)
        pass
    def pulse_off(self):
        # bt.PWM.stop(pindef.output_definitions['laser_port'])
        pass
    def play_stim(self, stimset, stimulus, channel=0):
        # stimset_name = stimset['name']
        filename =  '%s%s/%s%s'%(self.stimuli_dir,stimset['name'], stimulus, stimset['stims'][0]['file_type'])
        self.play_sound(filename,channel=channel)
        pass

    def play_sound(self, filename, channel = 0):
        # kill any workers
        while len(self.so_workers)>0:
            worker = self.so_workers.pop()
            if worker[0].is_alive():
                worker[1].value = 1;
                worker[0].join()

        filetype = filename[-4:]
        idx = self.sc_idx
        if not self.sc_out_idx is None:
           idx = self.sc_out_idx
        
        #if not self.pcm_out is None:
        #    p = so.sendwf2(self.pcm_out, filename, filetype, 44100, channel=channel)
        #else:
        p = so.sendwf(idx, filename, filetype, 44100, channel=channel)
        self.so_workers.append(p)
        pass

    def beep(self):
        self.play_sound('sounds/beep.wav')
        pass

    def beep_warning(self):
        self.play_sound('sounds/buzzer_quite.wav')
        pass

    def stop_sounds(self):
        while len(self.so_workers)>0:
            worker = self.so_workers.pop()
            if worker[0].is_alive():
                worker[1].value = 1;
                worker[0].join()
        pass

    def is_playing(self):
        is_playing = False
        for worker in self.so_workers:
            if worker[1].value == 0:
                is_playing = True
        return is_playing

    def connect_to_camera(self, camera_idx = 0, plot=False, bounds = None, exclusion_zones=None):
        if self.video_event_queue is None:
            pcap, ptrack, eventq, controlq, t = vt.start_tracking(camera_idx = camera_idx, plot = plot, bounds=bounds, exclusion_polys = exclusion_zones)
            self.video_event_queue = eventq
            self.video_capture_process = pcap
            self.video_tracking_process = ptrack
            self.video_control_queue = controlq
        pass

    def start_video_recording(self, filename_suffix = ""):
        if self.video_control_queue is None or self.video_event_process is None:
            pass
        else:
            filename = "%s/%s_%f_%s" % (self.media_outdir, self.birdname,self.current_time, filename_suffix)
            self.video_control_queue.put(["start", filename])

    def stop_video_recording(self):
        if self.video_control_queue is None:
            pass
        else:
            self.video_control_queue.put(["stop",""])

    def start_forced_audio_recording(self):
        self.audio_control_queue.put("start")

    def stop_forced_audio_recording(self):
        self.audio_control_queue.put("stop")

    def init_video(self):
        self.video_playback_object = vpt.PyGamePlayer()

    def play_video(self,fname):
        if self.video_playback_object is None:
            self.init_video()
        self.video_playback_object.send_movie(fname)

    def stop_video(self):
        self.video_playback_object.stop()

    def write_command(self, command):
        self.serial_io.write(unicode(command))
        self.serial_io.flush()

    def select_screen(self,screen):
        self.write_command('<o12=%d>' % screen)


##
def run_box(controller, box):
    # if not controller.ready_to_run:
    #     pass
    # if not box.ready_to_run:
    #     pass
    # initialize controller
    controller.box_state = 'go'
    controller.has_run = True
    controller.generate_file_name()
    controller.save_config_file()

    controller.box = box

    # print out params
    if debug:
        for key in sorted(controller.params.keys()):
            print key + ': ' + str(controller.params[key])
    # initialize box
    if box.recorder is not None:
        box.recorder.start()
        # time.sleep(2)
        # import ipdb; ipdb.set_trace()
    box.stimuli_dir = controller.params['stimuli_dir']
    box.query_events()
    box.light_on()
    box.feeder_off()
    box.beep()



#    try:
        # send loop
    main_loop(controller, box)
 #   except Exception as e:
        # if 'alsa' in e.str:
        #     # restart alsa
        #     main_loop(controller,box)
        # else:
  #      raise(e)

    # send loop
    # main_loop(controller, box)
    pass

def main_loop(controller, box):
    # generate the first trial and set that as the state
    controller.que_next_trial()
    controller.task_state = 'prepare_trial'
    controller.has_run = True
    # enter the loop
   # pdb.set_trace(a)
    last_time = box.current_time
    while controller.box_state == 'go':
        current_time = box.current_time
        loop_time = current_time - last_time
        last_time = current_time
        # query serial events since the last itteration
        events_since_last = box.query_events()
        
        # save loop times greator than tollerance as events
        if loop_time > time_tollerance:
            events_since_last.append((current_time, 'loop time was %e, exceeding tollerance of %e' % (loop_time, time_tollerance)))

        # run throgh loop itteration state machine
        events_since_last, trial_ended = loop.iterations[controller.params['mode']](controller, box, events_since_last)

        # save all the events that have happened in this loop to file
        controller.save_events_to_log_file(events_since_last)

        # if a trial eneded in this loop then store event, save events, generate new trial
        if trial_ended:
            controller.task_state = 'prepare_trial'
            controller.store_current_trial()
            controller.que_next_trial()
            # if box.current_time > last_bt_refresh + bt_refresh_interval:
                # box.refresh_bt()
                # last_bit_refresh = box.current_time

        if 'toggle_force_feed' in [event[1] for event in events_since_last]:
            if box.force_feed_up is False:
                box.force_feed_up = True
                box.feeder_on()
            else:
                box.force_feed_up = False
                box.feeder_off()

        if box.serial_c is not None:
            # other housecleaning:
            if current_time - box.last_sync_time > box.sync_period:
                box.sync()
                last_time = box.current_time




    # exit routine:
    pass

def load_and_verify_stimset(stimuli_dir, stim_name):
    """loads and verifys that the stimset 'stim_name', and checks that
    the stimset is properly formatted, that all stimuli exist, ext"""

    stim_dir = stimuli_dir + stim_name + '/'
    mat_fname = stim_dir + stim_name + '.mat'
    if not os.path.exists(stim_dir):
        raise Exception('No stim ' + stim_name + ' in ' + stimuli_dir)
    if os.path.exists(mat_fname):
        mat_contents= spio.loadmat(mat_fname,  struct_as_record=False)
    else:
        raise Exception('No .mat file in stimulus directory ' + 'stim_dir')
    try:
        stimset_out = {}
        stimset = mat_contents['stimset']
        stimset_out['name'] = stimset[0,0].name[0]
        stimset_out['numstims'] = stimset[0,0].numstims[0,0]
        stimset_out['samprate'] = stimset[0,0].samprate[0,0]
        stimset_out['stims'] = []
        for stim in stimset[0,0].stims[0]:
            stim_out = {}
            stim_out['name'] = stim.name[0]
           # stim_out['type'] = stim.type[0]
            stim_out['length'] = stim.length[0,0]
           # stim_out['onset'] = stim.onset[0,0]
           # stim_out['offset'] = stim.offset[0,0]

            # verify that song file exists and deduce file type
            if os.path.exists(stim_dir + stim_out['name'] + '.sng'):
                stim_out['file_type'] = '.sng'
            elif os.path.exists(stim_dir + stim_out['name'] + '.wav'):
                stim_out['file_type'] = '.wav'
            elif os.path.exists(stim_dir + stim_out['name'] + '.raw'):
                stim_out['file_type'] = '.raw'
            else:
                raise(Exception('Song file ' + stim_out['name'] + 'does not exist'))

            stimset_out['stims'].append(stim_out)

    except Exception as e:
        print 'Stimset ' + mat_fname + ' is not properly formatted'
        raise e
    return stimset_out



def parse_config(cfpath):
    config = ConfigParser.ConfigParser()
    config.read(cfpath)
    config_fid = open(cfpath)

    # set required parameters
    controller = BehaviorController()
    controller.config_file_contents = config_fid.read()
    controller.set_bird_name(config.get('run_params','birdname'))
    controller.params['mode'] = config.get('run_params','mode')
    controller.params['trial_generator'] = config.get('run_params','trial_generator')

    controller.stimset_names = []
    stimset_num = 0
    while True:
        if config.has_option('run_params','stimset_%d' % stimset_num):
            controller.stimset_names.append(config.get('run_params','stimset_%d' % stimset_num))
            stimset_num += 1
        else:
            break
    if len(controller.stimset_names) is 0:
        raise Exception('No Stimsets in config file')


    for key in controller.params.keys():
        if config.has_option('run_params', key):
            controller.params[key] = config.get('run_params', key)

    # set (overwrite) boolean parameters
    for param in ['withold_response']:
        if config.has_option('run_params', param):
            controller.params[param] = config.getboolean('run_params', param)

    for param in ['warn_feeder_off']:
        if config.has_option('run_params', param):
            controller.params[param] = config.getboolean('run_params', param)

    # set (overwrite) float parameters
    for param in ['feed_time', 'max_trial_length', 'timeout_period', 'pulse_width', 'pulse_period', 'laser_occurance', 'probe_occurance','isi_parameter', 'delay_time', 'center_bin_time', 'interstimulus_interval', 'nplaybacks_per_side', 'intertrial_interval', 'trigger_window', 'min_trigger_duration', 'max_trigger_entropy', 'max_stim_limit', 'min_trigger_power']:
        if config.has_option('run_params', param):
            controller.params[param] = config.getfloat('run_params', param)

    # set (overwrite) int parameters:
    for param in ['allowed_songs_per_session']:
        if config.has_option('run_params', param):
            controller.params[param] = config.getint('run_params', param)

    # set (overwrite) list parameters
    for param in ['stimset_occurance', 'set_times']:
        if config.has_option('run_params', param):
                controller.params[param] = json.loads(config.get('run_params',param))

    if controller.params['set_times'] != None:
        for set_time in controller.params['set_times']:
            controller.rewards_per_session[set_time] = 0
    # modify data_dir
    controller.params['data_dir'] = "/".join([controller.params['data_dir'], controller.birdname]) + "/"
    if not os.path.exists(controller.params['data_dir']):
        os.makedirs(controller.params['data_dir'])
    controller.load_stimsets()
    box = BehaviorBox()
    box.birdname = controller.birdname
    box.media_outdir = "/".join([controller.params['data_dir'], controller.birdname])
    if not os.path.exists(box.media_outdir):
        os.makedirs(box.media_outdir)

    # setup audio recorder
    if config.has_section('record_params'):
        if config.has_option('record_params','record_audio'):
            record_audio = config.getboolean('record_params','record_audio')
        else:
            record_audio = False
        if record_audio:
            box.recorder = ar.AudioRecord()
            for option in config.options('record_params'):
                if option == "record_audio":
                    pass
                elif option == "soundcard" or option=="sound_card":
                    attr = config.get('record_params', option)
                    box.recorder.set_sound_card(attr)
                elif option == "sound_card_out":
                    attr = config.get('record_params', option)
                    box.recorder.set_sound_card_out(attr)
                elif option in ["outdir", "birdname"]:
                    attr = config.get('record_params', option)
                    box.recorder.params[option] = attr
                elif option in ["chunk", "channel"]:
                    attr = config.getint('record_params', option)
                    box.recorder.params[option] = attr
                elif option == "audio_server":
                    attr = config.get('record_params', option)
                    if not attr in ['jack', 'alsa']:
                        raise(Exception('Error: %s is not a supported audio server' % attr))
                    #pdb.set_trace()
                    box.recorder.audio_server = attr
                else:
                    attr = config.getfloat('record_params', option)
                    box.recorder.params[option] = attr
            if config.has_section('run_params'):
                for option in config.options('run_params'):
                    if option in ["data_dir", "birdname"]:
                        attr = config.get("run_params", option)
                        box.recorder.params[option] = attr

            box.recorder.params['outdir'] = "/".join([box.recorder.params['data_dir'], box.recorder.params['birdname']])
    #               self.params['outdir'] = "/".join([self.params['outdir'], self.params['bird']])
            if not os.path.exists(box.recorder.params['outdir']):
                os.makedirs(box.recorder.params['outdir'])
            box.audio_event_queue=box.recorder.event_queue
            box.audio_control_queue = box.recorder.control_queue



    # setup video recorder and tracking
    if config.has_option('run_params','camera_idx'):
        camera_idx = config.getint('run_params','camera_idx')
        if config.has_option('run_params','camera_plot'):
            camera_plot= config.getboolean('run_params','camera_plot')
        else:
            camera_plot = False

        if config.has_option('run_params','camera_bounds'):
            camera_bounds = json.loads(config.get('run_params','camera_bounds'))
        else:
            camera_bounds = None

        if config.has_option('run_params', 'exclusion_zones'):
            exclusion_zones = json.loads(config.get('run_params', 'exclusion_zones'))
        else:
            exclusion_zones = None
        box.connect_to_camera(camera_idx=camera_idx, plot=camera_plot, bounds = camera_bounds, exclusion_zones=exclusion_zones)

    if config.has_option('run_params','video_playback'):
        video_playback = config.getboolean('run_params','video_playback')
        if video_playback:
            box.init_video()
        else:
            pass
    else:
        pass


    # set arduino model if
    if config.has_option('run_params','arduino_model'):
        arduino_model = config.get('run_params','arduino_model')
        box.arduino_model = arduino_model
    else:
        pass


    if config.has_option('run_params','box'):     # if box is set, then use the select box options for soundcard and serial connection
        box.activate_box(config.get('run_params','box'))
    else:                                          # otherwise use soundcard and or arduino_port options
        if config.has_option('run_params','soundcard'):
            sc_idx = config.getint('run_params','soundcard')
            box.select_sound_card(sc_idx)
        else:
            box.select_sound_card()
            # box.select_serial_port()

        if config.has_option('run_params', 'sound_card_out'):
            attr = config.get('run_params', 'sound_card_out')
            box.select_sound_card(attr, playback=True) 
        if config.has_option('run_params','arduino_port'):
            arduino_port = config.get('run_params','arduino_port')
            box.select_serial_port(port=arduino_port)
            box.select_screen(0)
            box.select_screen(1)
        else:
            pass

    # set any box params
    for param in ['trigger_value']:
        if config.has_option('run_params', param):
            attr = config.getfloat('run_params',param)
            setattr(box,param,attr)


   
    # run the box
    run_box(controller, box)


#    import cProfile
#    command = """run_box(controller,box)"""
#    cProfile.runctx(command, globals(), locals(), filename = 'test.profile')

if __name__=='__main__':
    ## Settings (temporary as these will be queried from GUI)
    import sys
    if len(sys.argv) <= 1:
        raise(Exception('No configuration file passed'))
    else:
        cfpath = sys.argv[1]

    parse_config(cfpath)
