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
import lib.serial_tools as st
import lib.usb_tools as ut
import lib.arduino_tools as at
import loop_iterations as loop
import trial_generators as trial


# from pyfirmata import Arduino, util
baud_rate = 19200
time_tollerance = 500e-3
debug = True
beep = False
## Settings 
mode_definitions = loop.iterations.keys()

# input_definitions = {2: ['song_trigger'], 
#                      3: ['response_trigger', 'response_a'],
#                      4: ['response_trigger', 'response_b']}

# output_definitions = {'reward_port': 12}
# trigger_value = 1
default_stimuli_dir = '/home/jknowles/data/doupe_lab/stimuli/'
default_data_dir = '/home/jknowles/data/doupe_lab/behavior/'

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

        self.params['withold_response'] = False

        # initializethe trial variables
        self.params['trial_generator'] = 'standard'

        # trial
        self.params['probe_occurance'] = 20



    def set_bird_name(self,birdname):
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
            self.event_count += 1
            fid.write("%d:%s\n"%(self.event_count, str(event)))
            if debug:
                print "%s: %d %s"%(box.box_name, self.event_count, str(event))
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

class BehaviorBox(object):
    """this object holds the present state of the behavior Arduino
    and contains the methods to change the pins of the box"""
    def __init__(self):
        # 

        self.stimuli_dir = None

        self.input_definitions = {2: ['song_trigger'], 
                             3: ['response_trigger', 'response_a'],
                             4: ['response_trigger', 'response_b']}
        self.output_definitions = {'reward_port': 12,
                                    'light_port': 11}
        self.trigger_value = 1

        self.box_zero_time = 0
        self.last_sync_time = 0
        self.sync_period = 60*10
        self.serial_port = None
        self.serial_device_id = None
        self.serial_c = None
        self.serial_io = None
        self.sc_idx = None

        self.serial_buffer = ""

        self.box_name = None

        self.so_workers = []

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
            self.select_serial_port(box_data[1])
            self.select_sound_card(box_data[2])
            self.box_name = box_data[0]
            print 'Connected to %s' % box_data[0]
        else:
            raise(Exception('%s not connected' % box))

    def select_serial_port(self, port = None):
        list_of_ports = st.return_list_of_usb_serial_ports()
        if port == None:
            print 'Select desired port from list below:'
            for k,port in enumerate(list_of_ports):
                print '[%d] port: %s serial# %s' % (k,port[0], port[1])
            # x = input('Enter Number: ')
            x = 0
            self.serial_port = list_of_ports[x][0]
            self.serial_device_id = list_of_ports[x][1]
        else:
            self.serial_port = port;
        result = self.connect_to_serial_port()
        return result

    def connect_to_serial_port(self):
        try:
            self.serial_c = serial.Serial(self.serial_port, baud_rate, parity = serial.PARITY_NONE, bytesize = serial.EIGHTBITS, stopbits = serial.STOPBITS_ONE, xonxoff = False, rtscts = False, timeout = False)
            self.serial_c.setDTR(False)
            time.sleep(1)
            self.serial_c.flushInput()
            self.serial_c.flushOutput()
            time.sleep(1)
            self.serial_c.setDTR(True)
            self.serial_io = io.TextIOWrapper(io.BufferedRWPair(self.serial_c, self.serial_c, 20), line_buffering = False, newline='\r')  
            time.sleep(2)
            return self.sync()
        except:
            self.reload_arduino_firmware()
            return self.connect_to_serial_port()
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

    # def connect_to_sound_card(self, cardidx):
    #     self.sc_object = alsaaudio.PCM(type=alsaaudio.PCM_PLAYBACK, mode=alsaaudio.PCM_NORMAL, card='hw:%d,0'%cardidx)
    #     self.sc_object.setrate(44100)

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
        if port in self.input_definitions.keys():
            if state == self.trigger_value:
                event = [box_time] + self.input_definitions[port]
            else: return None
        else: return None
        return tuple(event)

    def query_events(self, timeout = 0):
        events_since_last = []
        try:
            if timeout != self.serial_c.timeout:
                self.serial_c.timeout = timeout
            # read any new input into the buffer
            self.serial_buffer += self.serial_io.read()
        except st.SerialException as e:
            raise e

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


    def write_command(self, command):
        self.serial_io.write(unicode(command))
        self.serial_io.flush()

    def feeder_on(self):
        command = '<o%d=1>'%self.output_definitions['reward_port']
        self.write_command(command)

    def feeder_off(self):
        command = '<o%d=0>'%self.output_definitions['reward_port']
        self.write_command(command)
    def light_on(self):
        command = '<o%d=0>'%self.output_definitions['light_port']
        self.write_command(command)
    def light_off(self):
        command = '<o%d=1>'%self.output_definitions['light_port']
        self.write_command(command)
    def pulse_on(self):
        command = '<p=2>'
        self.write_command(command)

    def pulse_off(self):
        command = '<p=0>'
        self.write_command(command)

    def pulse_on_trigger(self):
        command = '<p=1>'
        self.write_command(command)

    def sync(self):

        send_time = self.current_time
        self.write_command('<sync>')
        events = []
        count = 0
        events = self.query_events(timeout = 2)
        sync_time = None
        for event in events:
            if len(event) > 1 and event[1]=='sync':
                sync_time = float(event[0])
        if sync_time != None:
            self.box_zero_time = send_time - float(sync_time)/1000
            self.last_sync_time = self.current_time;
            return True
        else:
            raise(Exception('Sync not successful'))
        return True

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
            print worker[1].value


    def reload_arduino_firmware(self):
        at.build_and_upload(self.serial_port)

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
        for key in controller.params:
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
        controller.task_state = 'waiting_for_trial'
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
            events_since_last, trial_ended = loop.iterations[controller.params['mode']](controller, box, events_since_last)
            # save all the events that have happened in this loop to file
            controller.save_events_to_log_file(events_since_last)
            # if a trial eneded in this loop then store event, save events, generate new trial
            if trial_ended:
                controller.task_state = 'waiting_for_trial'
                controller.store_current_trial()
                controller.que_next_trial()

            # other housecleaning:
            if current_time - box.last_sync_time > box.sync_period:
                box.sync()
            # exit routine:
        pass
    except Exception as e:
        # crash handeling
        controller.save_events_to_log_file([(box.current_time, "Error: %s," % (str(e)))])# save crash event
        box.serial_c.close() 
        box.connect_to_serial_port() # reconnect to box
	box.light_on()
        controller.save_events_to_log_file([(box.current_time, "serial connection restablished")])
        
        # renter loop
        main_loop(controller, box)


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

    # set (overwrite) float parameters
    for param in ['feed_time', 'max_trial_length', 'timeout_period']:
        if config.has_option('run_params', param):
            controller.params[param] = config.getfloat('run_params', param)



    controller.load_stimsets()
    box = BehaviorBox()
    if config.has_option('run_params','box'):
        box.select_box(config.get('run_params','box'))
    else:
        box.select_sound_card()
        box.select_serial_port()

    run_box(controller, box)
    # import cProfile
    # command = """run_box(controller,box)"""
    # cProfile.runctx(command, globals(), locals(), filename = 'test.profile')

