import scipy as sp
import numpy as np
from scipy import io as spio
import os
import serial
from serial.tools import list_ports
import time
import datetime
import random 
import io
import alsaaudio

import soundout_tools as so

# from pyfirmata import Arduino, util
debug = True

## Settings (temporary as these will be queried from GUI)
stimuli_dir = '/data/doupe_lab/stimuli/'
data_dir = '/data/temp/'
birdname = 'testbird'

class BehaviorController(object):
    def __init__(self):
        self.birdname = birdname 

        # save the date and time 
        self.initial_date = datetime.datetime.now()

        # file names ext
        self.base_filename = None
        self.generate_file_name()
        self.log_fid = None
        self.trial_fid = None

        # initialize the state variables
        self.task_state = None
        # initialize the task variables
        self.mode = None
        self.stimset_names = []
        self.stimsets = []
        self.expected_responses = ['response_a', 'response_b']


        # initialize the task parameters 
        self.timeout_period = 5; # timeout (punishment) time in seconds
        self.max_trial_length = 10; # maximum trial time in seconds
        self.feed_time = 5;


        # initializethe trial variables
        self.current_trial = None
        self.completed_trials = []

        # to add: self.trial_block = []
        self.random_stimuli = True

    def generate_file_name(self):
        if self.base_filename is not None:
            return self.filename
        basename = '%s_%04d%02d%02d' %(self.birdname,self.initial_date.year,self.initial_date.month,self.initial_date.day) 
        idx = 0
        while os.path.exists('%s%s_%d.log'%(data_dir,basename,idx)):
            idx +=1
        name = '%s_%d'%(basename,idx)
        self.base_filename = name
        pass

    @property
    def n_trials(self):
        return len(self.completed_trials) + 1

    def load_stimsets(self):
        if len(self.stimset_names) < 2:
            raise Exception('Error: less than 2 stimset names set')
        self.stimsets = []
        for name in self.stimset_names:
            self.stimsets.append(load_and_verify_stimset(name))
        pass

    def store_current_trial(self):
        self.completed_trials.append(self.current_trial)
        self.current_trial = None
        pass

    def list_all_stimuli(self):
        stimuli = []
        for kstimset, stimset in enumerate(self.stimsets):
            stimuli.extend([(kstimset, kstim, stim['name']) for kstim,stim in enumerate(stimset['stims'])])
        return stimuli

    def generate_next_trial(self):
        if self.current_trial != None:
            self.store_current_trial()
        # initialize
        trial = {}
        stim_list = self.list_all_stimuli()
        # pick the stimset and the stimulus
        idx = random.randint(0, len(stim_list)-1)
        trial['stimulus'] = stim_list[idx][2]
        trial['stimset_idx'] = stim_list[idx][0]
        trial['stimset'] = self.stimset_names[trial['stimset_idx']]
        trial['correct_answer'] = self.expected_responses[stim_list[idx][0]]
        self.current_trial = trial
        pass

    def return_log_fid(self):
        if self.log_fid == None:
            self.log_fid = open('%s%s.log'% (data_dir,self.base_filename), 'w')
        return self.log_fid
    def return_events_fid(self):
        if self.trial_fid == None:
            self.trial_fid = open('%s%s.trial'% (data_dir,self.base_filename), 'w')
        return self.trial_fid

    def save_events_to_log_file(self,  events_since_last):
        fid = self.return_log_fid()
        fid.writelines(["%s\n"%str(event) for event in events_since_last])
        fid.flush()
        pass

    def save_trials_to_file(self):
        fid = self.return_events_fid()

        pass

class BehaviorBox(object):
    """this object holds the present state of the behavior Arduino
    and contains the methods to change the pins of the box"""
    def __init__(self):
        # 

        # port settings
        self.input_definitions = {2: ['song_trigger'], 
                                  3: ['response_trigger', 'response_a'],
                                  4: ['response_trigger', 'response_b']}
        self.output_definitions = {'reward_port': 12}
        self.trigger_value = 1

        self.box_zero_time = 0
        self.serial_port = None
        self.serial_connection = None
        self.serial_io = None
        self.select_serial_port()
        self.connect_to_serial_port()

        # 
        self.sc_idx = None
        #self.sc_object = None
        self.select_sound_card()
        


    @property
    def current_time(self):
        return time.time()

    def select_serial_port(self):
        list_of_ports = return_list_of_usb_serial_ports()
        print 'Select desired port from list below:'
        for k,port in enumerate(list_of_ports):
            print '[%d] %s' % (k,port)
        x = input('Enter Number: ')
        self.serial_port = list_of_ports[x]

    def connect_to_serial_port(self):
        self.serial_c = serial.Serial(self.serial_port, 115200, parity = serial.PARITY_NONE, xonxoff = True, rtscts = True, dsrdtr = True, timeout = False)
        self.serial_io = io.TextIOWrapper(io.BufferedRWPair(self.serial_c, self.serial_c, 1), line_buffering = False)  
        time.sleep(2)
        self.sync()

    def select_sound_card(self):
        list_of_cards = alsaaudio.cards()
        print 'Select desired card from list below:'
        for k,card in enumerate(list_of_cards):
            print '[%d] %s' % (k,card)
        idx = input('Enter Number: ')
        self.sc_idx = idx

    # def connect_to_sound_card(self, cardidx):
    #     self.sc_object = alsaaudio.PCM(type=alsaaudio.PCM_PLAYBACK, mode=alsaaudio.PCM_NORMAL, card='hw:%d,0'%cardidx)
    #     self.sc_object.setrate(44100)

    def parse_event_from_line(self,line):
        line = line.strip('\n')
        if len(line)>0 and line[0]=='<' and line[-1]=='>': # this needs better care
            line_parts = line[1:-1].split('-')
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
        self.serial_c.timeout = timeout
        try:
            # query box to see if there are any serial changes
            serial_lines = self.serial_io.readlines()
        except:
            self.serial_c.close()
            self.connect_to_serial_port()
            #self.serial_io.
            return [(self.current_time, 'bad_read','may_have_missed_serial_events')]
        for line in serial_lines:
            event = self.parse_event_from_line(line)
            if event != None:
                events_since_last.append(event)
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

    def sync(self):
        send_time = self.current_time
        self.write_command('<sync>')
        events = []
        count = 0
        events = self.query_events(timeout = 2)
        for event in events:
            if len(event) > 1 and event[1]=='sync':
                sync_time = float(event[0])
        self.box_zero_time = send_time - float(sync_time)/1000

    def load_song(self, dir, file_name):
        fid = open('%s%s/%s'%(stimuli_dir,dir,file_name))
        ipdb.set_trace()

    def play_song(self, stimulus):
        # stimset_name = stimset['name']
        # song_data = self.load_song(stimset['name'],'%s%s'%(stimulus,stimset['stims'][0]['file_type']))
        so.sendwave(self.sc_idx, '/home/jknowles/wf_with_spikes.wav')
        pass  





##
def run_box(controller, box):
    # initialize controller
    controller.box_state = 'go'
    # initialize box
    box.query_events()
    # send loop
    main_loop(controller, box)
    pass

def main_loop(controller, box):
    # try:
    # generate the first trial and set that as the state
    controller.generate_next_trial()
    controller.task_state = 'waiting_for_trial'

    # enter the loop
    while controller.box_state == 'go':

        # record any events that have happened on the box
        events_since_last = box.query_events()
        events_since_last_names = [event[1] for event in events_since_last]
        trial_ended = False
        # examine what events have happened and trigger new ones, depending on box state
        if controller.task_state == 'waiting_for_trial':
            if 'song_trigger' in events_since_last_names:
                box.play_song(controller.current_trial['stimulus'])
                controller.current_trial['start_time'] = box.current_time
                events_since_last.append((box.current_time, 'song_playback', controller.current_trial['stimulus']))
                controller.task_state = 'waiting_for_response'

        # if a trial is ongoing then look for responses
        elif controller.task_state == 'waiting_for_response':
            # if there is a response
            if 'response_trigger' in events_since_last_names:
                event_idx = events_since_last_names.index('response_trigger')
                controller.current_trial['response_time'] = box.current_time
                ## if anwser is correct
                if  events_since_last[event_idx][2] == controller.current_trial['correct_answer']:
                    controller.current_trial['result'] = 'correct'
                    controller.task_state = 'reward'
                    events_since_last.append((box.current_time, 'reward_start'))
                    box.feeder_on()
                ## otherwise anwser is incorrect 
                else:
                    controller.current_trial['result'] = 'incorrect'
                    controller.task_state = 'time_out'
                    events_since_last.append((box.current_time, 'timeout_start'))

            # if no response and trial has timed out
            elif box.current_time > controller.current_trial['start_time'] + controller.max_trial_length:
                controller.current_trial['result'] = 'no_response'
                events_since_last.append((box.current_time, 'no_response'))
                trial_ended = True

        # if the box is in time_out state (after an incorrect trial) 
        elif controller.task_state == 'time_out':
            if box.current_time > controller.current_trial['response_time'] + controller.timeout_period:
                events_since_last.append((box.current_time, 'timout_end'))
                trial_ended = True
        # if the reward period is over
        elif controller.task_state == 'reward':
            if box.current_time > controller.current_trial['response_time'] + controller.feed_time:
                box.feeder_off()
                events_since_last.append((box.current_time, 'reward_end'))
                trial_ended = True

        # save all the events that have happened in this loop to file
        controller.save_events_to_log_file(events_since_last)
        if debug:
            for event in events_since_last:
                print event

        # if a trial eneded in this loop then store event, save events, generate new trial
        if trial_ended:
            controller.task_state = 'waiting_for_trial'
            controller.store_current_trial()
            controller.save_trials_to_file()
            controller.generate_next_trial()


    # except Exception as e:
    #     raise e

        # get any feeder variables

        # 

def load_and_verify_stimset(stim_name):
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
            stim_out['type'] = stim.type[0]
            stim_out['length'] = stim.length[0,0]
            stim_out['onset'] = stim.onset[0,0]
            stim_out['offset'] = stim.offset[0,0] 

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
    for port in list_of_ports: print port
    return filter(lambda x: 'ACM' in x, list_of_ports)




if __name__=='__main__':
    ## Settings (temporary as these will be queried from GUI)
    stimset_a = 'syl_discrim_v1_stimset_a'
    stimset_b = 'syl_discrim_v1_stimset_b_6'
    # # initialize controller
    controller = BehaviorController()
    controller.stimset_names.apepend(stimset_a)
    controller.stimset_names.apepend(stimset_b)
    controller.load_stimsets()
    box = BehaviorBox()
    run_box(controller, box)
