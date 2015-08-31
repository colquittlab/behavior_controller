
import sys
import os
import pdb
import time
import ConfigParser

sys.path.append(os.path.expanduser("~/src/behavior_controller"))
import behavior_controller as bc
import lib.usb_tools as ut
import lib.serial_tools as st

def init_box(box, box_name):
        #pdb.set_trace()
#        list_of_boxes = ut.return_list_of_boxes()
        list_of_arduinos = st.return_list_of_named_arduinos()
        box_num = box_name.split("_")[1]
        arduino_nums = [x.split("_")[1] for x in list_of_arduinos]
        if box_num in [a for a in arduino_nums]:
            idx = [a for a in arduino_nums].index(box_num)
            #box_data = list_of_boxes[idx]
            box.select_serial_port(list_of_arduinos[idx])
#            self.select_sound_card(box_data[2])
            box.box_name = box_name
            print 'Connected to %s' % box_name
#            print 'Soundcard index %s' % self.sc_idx
#            print box_data[1] # GK
#            print box_data[2] # GK
        else:
            raise(Exception('%s not connected' % box_name))

#def test_iteration(controller, box, events_since_last):

def run_loop(controller, box):
    
    while True:
        time.sleep(.05)
        events_since_last = box.query_events()
        events_since_last_names = [event[1] for event in events_since_last]
        if 'song_trigger' in events_since_last_names:
            print "Triggered."
#        events_since_last, trial_ended = test_iteration(controller, box, events_since_last)

def main(argv):
    
#    box = bc.BehaviorBox()

    if len(sys.argv) <= 1:
        raise(Exception('No configuration file passed'))
    else:
        cfpath = sys.argv[1]
    config = ConfigParser.ConfigParser() 
    config.read(cfpath)

    controller = bc.BehaviorController()
    box = bc.BehaviorBox()
    if config.has_option('run_params','box'):
        init_box(box, config.get('run_params','box'))
    else:
        box.select_sound_card()
        box.select_serial_port()

    if config.has_option('run_params', 'arduino_model'):
        setattr(box,'arduino_model',config.get('run_params', 'arduino_model'))

    box.query_events()

    run_loop(controller, box)

if __name__ == "__main__":
    main(sys.argv)
