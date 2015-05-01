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

import lib.soundout_tools as so
# import lib.serial_tools as st
# import lib.arduino_tools as at
import lib.usb_tools as ut
import loop_iterations as loop
import trial_generators as trial
import lib.bone_tools as bt
import lib.pin_definitions as pindef

# from pyfirmata import Arduino, util
time_tollerance = 50e-3
debug = True
beep = False
## Settings 
mode_definitions = loop.iterations.keys()
default_stimuli_dir = '/home/doupelab/data/stimuli/'
default_data_dir = '/home/doupelab/data/behavior/'

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
        self.timeout_count = 0

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

        # parameters for playback mode
        self.params['delay_time'] = 5
        self.params['isi_distribution'] = 'exponential'
        self.params['isi_parameter'] = 10

        
        # stimset occurance
        self.Aocc = 0.5
        self.Bocc = 1.0 - self.Aocc



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
        if len(self.stimset_names) < 2:
            raise Exception('Error: less than 2 stimset names set')
        self.stimsets = []
        for name in self.stimset_names:
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
        if self.current_trial != None:
            self.store_current_trial()
        if len(self.trial_block) < 1:
            self.trial_block = trial.generators[self.params['trial_generator']](self)
        self.current_trial = self.trial_block.pop(0)
        pass

    def store_current_trial(self):
        self.completed_trials.append(self.current_trial)
        self.save_trial_to_file(self.current_trial)
        self.current_trial = None
        pass

    def return_log_fid(self):
        if self.log_fid == None:
            self.log_fid = open('%s%s.log'% (self.params['data_dir'],self.base_filename), 'w')
        return self.log_fid

    def return_events_fid(self):
        if self.trial_fid == None:
            self.trial_fid = open('%s%s.trial'% (self.params['data_dir'],self.base_filename), 'w')
        return self.trial_fid

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

        pass

    def save_events_to_log_file(self,  events_since_last):
        fid = self.return_log_fid()
        for event in events_since_last:
            # tally counts from events
            self.event_count += 1
            if event[1] == "reward_start":
                self.reward_count += 1
            if event[1] == "timeout_start":
                self.timeout_count += 1

            fid.write("%d:%s\n"%(self.event_count, str(event)))
            if debug:
                #print "%s: %d %s"%(box.box_name, self.event_count, str(event))
                print "%s events:%d, trials:%d, rewards:%d, tos:%d, %s"%(box.box_name, self.event_count, self.n_trials, self.reward_count, self.timeout_count, str(event)) #GK
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

    def calculate_performance_statistics(self, n_trials_back = None):
        stats = {}
        stats['by_stimset'] = []
        if n_trials_back != None:
            if len(self.completed_trials) > n_trials_back:
                relevant_trials = self.completed_trials[len(self.completed_trials) - n_trials_back:]
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
        # count events in trials
        for trial in relevant_trials:
            if trial['result'] == 'correct':
                stats['by_stimset'][trial['stimset_idx']]['n_correct'] += 1
            elif trial['result'] == 'incorrect':
                stats['by_stimset'][trial['stimset_idx']]['n_incorrect'] += 1
            elif trial['result'] == 'haulted':
                stats['by_stimset'][trial['stimset_idx']]['n_haulted'] += 1
            elif trial['result'] == 'no_response':
                stats['by_stimset'][trial['stimset_idx']]['n_noresponse'] += 1
        # calculate statisics for each stimset
        for stimset_idx in range(0, len(self.stimsets)):
            if (stats['by_stimset'][stimset_idx]['n_correct'] + stats['by_stimset'][stimset_idx]['n_incorrect']) == 0:
                stats['by_stimset'][stimset_idx]['p_correct'] = 0
            else:
                stats['by_stimset'][stimset_idx]['p_correct'] = float(stats['by_stimset'][stimset_idx]['n_correct']) / (stats['by_stimset'][stimset_idx]['n_correct'] + stats['by_stimset'][stimset_idx]['n_incorrect'])
        return stats    
        

class BehaviorBox(object):
    """this object holds the present state of the behavior Arduino
    and contains the methods to change the pins of the box"""
    def __init__(self):
        # 

        self.stimuli_dir = None
        self.serial_buffer = ""
        self.box_name = None
        self.so_workers = []
        self.pulse_state = 0

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

    @property
    def current_time(self):
        return time.time()

    def select_box(self, box):
        list_of_boxes = ut.return_list_of_boxes()
        if box in [b[0] for b in list_of_boxes]:
            idx = [b[0] for b in list_of_boxes].index(box)
            box_data = list_of_boxes[idx]
            # self.select_serial_port(box_data[1])
            self.select_sound_card(box_data[2])
            self.box_name = box_data[0]

    def return_list_of_sound_cards(self):
        return so.list_sound_cards()

    def select_sound_card(self, cardname = None):
        list_of_cards = self.return_list_of_sound_cards()
        if cardname == None:
            print 'Select desired card from list below:'
            for k,card in enumerate(list_of_cards):
                print '[%d] %s' % (k,card)
            idx = input('Enter Number: ')
            #idx = len(list_of_cards)-1
        else:
            idx = list_of_cards.index(cardname)
        self.sc_idx = idx
        self.beep()

    def query_events(self, timeout = 0):
        events_since_last = []
        while len(bt.event_buffer) > 0:
            event = bt.event_buffer.pop(0)
            event_out = [event[0]]
            event_out.extend(pindef.input_definitions[event[1]])
            events_since_last.append(tuple(event_out))
        return events_since_last
    def feeder_on(self):
        bt.set_output_list(pindef.output_definitions['feeder_port'], 0)
    def feeder_off(self, do_warning=False):
        if do_warning:
            self.beep_warning()
            time.sleep(1)
            pass
        bt.set_output_list(pindef.output_definitions['feeder_port'], 1) 
    def light_on(self):
        bt.set_output_list(pindef.output_definitions['light_port'], 0)
    def light_off(self):
        bt.set_output_list(pindef.output_definitions['light_port'], 1)
    def pulse_on(self, freq=100, duty=50):
        bt.PWM.start(pindef.output_definitions['laser_port'], duty, freq, 1)
    def pulse_off(self):
        bt.PWM.stop(pindef.output_definitions['laser_port'])
        bt.PWM.cleanup()
    def play_stim(self, stimset, stimulus):
        # stimset_name = stimset['name']
        filename =  '%s%s/%s%s'%(self.stimuli_dir,stimset['name'], stimulus, stimset['stims'][0]['file_type'])
        self.play_sound(filename)
        pass  

    def play_sound(self, filename):
        # kill any workers
        while len(self.so_workers)>0:
            worker = self.so_workers.pop()
            if worker[0].is_alive():
                worker[1].value = 1;
                worker[0].join()

        filetype = filename[-4:]
        p = so.sendwf(self.sc_idx, filename, filetype, 44100)
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

    # print out params
    if debug:
        for key in sorted(controller.params.keys()):
            print key + ': ' + str(controller.params[key])
    # initialize box
    box.stimuli_dir = controller.params['stimuli_dir']
    box.query_events()
    box.light_on()
    # send loop
    main_loop(controller, box)
    pass

def main_loop(controller, box):
    try:
    
        # generate the first trial and set that as the state
        controller.que_next_trial()
        controller.task_state = 'prepare_trial'
        controller.has_run = True
        # enter the loop
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
        # exit routine:
        pass


    except Exception as e:
	raise(e)

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

if __name__=='__main__':
    ## Settings (temporary as these will be queried from GUI)
    import sys
    if len(sys.argv) <= 1:
        raise(Exception('No configuration file passed'))
    else:
        cfpath = sys.argv[1]

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
    controller.stimset_names.append(config.get('run_params','stimset_0'))
    controller.stimset_names.append(config.get('run_params','stimset_1'))
    
    # set optional paramters
    if config.has_option('run_params','stimset_2'):
        controller.stimset_names.append(config.get('run_params','stimset_2'))

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
    for param in ['feed_time', 'max_trial_length', 'timeout_period', 'pulse_width', 'pulse_period', 'laser_occurance', 'probe_occurance','isi_parameter', 'delay_time']:
        if config.has_option('run_params', param):
            controller.params[param] = config.getfloat('run_params', param)

    # set (overwrite) list parameters
    for param in ['stimset_occurance']:
        if config.has_option('run_params', param):
                controller.params[param] = json.loads(config.get('run_params',param))

    controller.load_stimsets()
    box = BehaviorBox()
    if config.has_option('run_params','box'):
        box.select_box(config.get('run_params','box'))
    else:
        box.select_sound_card()
        box.select_serial_port()

    # set any box params
    for param in ['trigger_value']:
        if config.has_option('run_params', param):
            attr = config.getfloat('run_params',param)
            setattr(box,param,attr)
    # run the box
    run_box(controller, box)


    # import cProfile
    # command = """run_box(controller,box)"""
    # cProfile.runctx(command, globals(), locals(), filename = 'test.profile')

