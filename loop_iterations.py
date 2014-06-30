import numpy as np
import scipy as sp
import time


## iterations and generators


# the iterations and for each mode are loded into the mode dict
iterations = {}

def discrimination_iteration(controller, box, events_since_last):
    """ This function runs int the main loop in discrimination mode"""
    # record any events that have happened on the box     
    events_since_last_names = [event[1] for event in events_since_last]
    trial_ended = False

    # make any initial parameters
    if controller.task_state == 'prepare_trial':
        controller.task_state = 'waiting_for_trial'

    # examine what events have happened and trigger new ones, depending on box state
    if controller.task_state == 'waiting_for_trial':
        if 'song_trigger' in events_since_last_names:
            box.play_stim(controller.stimsets[controller.current_trial['stimset_idx']], controller.current_trial['stimulus'])
            controller.current_trial['start_time'] = box.current_time
            events_since_last.append((box.current_time, 'song_playback', controller.current_trial['stimulus']))
            controller.task_state = 'playing_song'

    # if song is playing and responses are ignored during song
    elif controller.task_state == 'playing_song':
        if controller.params['withold_response']:
            # if there is a response
            if 'response_trigger' in events_since_last_names:
                box.stop_sounds()
                events_since_last.append((box.current_time, 'response_during_song_playback_haulted'))
                controller.current_trial['result'] = 'haulted'
                controller.current_trial['response_time'] = box.current_time
                trial_ended = True
            if box.current_time > controller.current_trial['start_time'] + controller.current_trial['stim_length']:
                controller.task_state = 'waiting_for_response'
        else:
            if box.current_time > controller.current_trial['start_time'] + controller.params['minimum_response_time']:
                controller.task_state = 'waiting_for_response'


    # if a trial is ongoing then look for responses
    elif controller.task_state == 'waiting_for_response':
        if controller.params['withold_response']:
            timeout_time = controller.current_trial['start_time'] + controller.current_trial['stim_length'] + controller.params['max_trial_length']
        else:
            timeout_time = controller.current_trial['start_time'] + controller.params['max_trial_length']

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
                if controller.params['timeout_light']:
                    box.light_off()
                    events_since_last.append((box.current_time, 'light_off'))

        # if no response and trial has timed out
        elif box.current_time > timeout_time:
            controller.current_trial['result'] = 'no_response'
            events_since_last.append((box.current_time, 'no_response'))
            trial_ended = True

    # if the box is in time_out state (after an incorrect trial) 
    elif controller.task_state == 'time_out':
        if box.current_time > controller.current_trial['response_time'] + controller.params['timeout_period']:
            box.light_on()
            events_since_last.append((box.current_time, 'timout_end'))
            if controller.params['timeout_light']:
                box.light_on()
                events_since_last.append((box.current_time, 'light_on'))
            trial_ended = True
    # if the reward period is over
    elif controller.task_state == 'reward':
        if box.current_time > controller.current_trial['response_time'] + controller.params['feed_time']:
            box.feeder_off()
            events_since_last.append((box.current_time, 'reward_end'))
            trial_ended = True
    return events_since_last, trial_ended
iterations['discrimination'] = discrimination_iteration

def discrimination_singleport_iteration(controller, box, events_since_last):
    """ This function runs int the main loop in discrimination mode"""
    # record any events that have happened on the box     
    events_since_last_names = [event[1] for event in events_since_last]
    trial_ended = False

    # make any initial parameters
    if controller.task_state == 'prepare_trial':
        controller.task_state = 'waiting_for_trial'
    # examine what events have happened and trigger new ones, depending on box state
    if controller.task_state == 'waiting_for_trial':
        if 'song_trigger' in events_since_last_names:
            box.play_stim(controller.stimsets[controller.current_trial['stimset_idx']], controller.current_trial['stimulus'])
            controller.current_trial['start_time'] = box.current_time
            events_since_last.append((box.current_time, 'song_playback', controller.current_trial['stimulus']))
            if controller.params['withold_response'] is True:
                controller.task_state = 'playing_song'
            else:
                controller.task_state = 'waiting_for_response'
    # if song is playing and responses are ignored during song
    elif controller.task_state == 'playing_song':
        # if there is a response
        # if 'response_trigger' in events_since_last_names:
        #     box.stop_sounds()
        #     events_since_last.append((box.current_time, 'response_during_song_playback_haulted'))
        #     controller.current_trial['result'] = 'haulted'
        #     controller.current_trial['response_time'] = box.current_time
        #     trial_ended = True
        if box.current_time > controller.current_trial['start_time'] + controller.current_trial['stim_length']:
            controller.task_state = 'waiting_for_response'
    # if a trial is ongoing then look for responses
    elif controller.task_state == 'waiting_for_response':
        if controller.params['withold_response']:
            timeout_time = controller.current_trial['start_time'] + controller.current_trial['stim_length'] + controller.params['max_trial_length']
        else:
            timeout_time = controller.current_trial['start_time'] + controller.params['max_trial_length']

        # if there is a response
        if 'song_trigger' in events_since_last_names:
            event_idx = events_since_last_names.index('song_trigger')
            controller.current_trial['response_time'] = box.current_time
            ## if anwser is correct
            if  "response_a" == controller.current_trial['correct_answer']:
                controller.current_trial['result'] = 'correct'
                controller.task_state = 'reward'
                events_since_last.append((box.current_time, 'reward_start'))
                 
                box.feeder_on()
            ## otherwise anwser is incorrect 
            else:
                controller.current_trial['result'] = 'incorrect'
                controller.task_state = 'time_out'
                events_since_last.append((box.current_time, 'timeout_start'))
                if controller.params['timeout_light']:
                    box.light_off()
                    events_since_last.append((box.current_time, 'light_off'))

        
        
        # if no response and trial has timed out
        elif box.current_time > timeout_time:
            controller.current_trial['result'] = 'no_response'
            events_since_last.append((box.current_time, 'no_response'))
            trial_ended = True

    # if the box is in time_out state (after an incorrect trial) 
    elif controller.task_state == 'time_out':
        if box.current_time > controller.current_trial['response_time'] + controller.params['timeout_period']:
            events_since_last.append((box.current_time, 'timout_end'))
            trial_ended = True
            if controller.params['timeout_light']:
                box.light_on()
                events_since_last.append((box.current_time, 'light_on'))

    # if the reward period is over
    elif controller.task_state == 'reward':
        if box.current_time > controller.current_trial['response_time'] + controller.params['feed_time']:
            box.feeder_off()
            events_since_last.append((box.current_time, 'reward_end'))
            trial_ended = True
    return events_since_last, trial_ended
iterations['discrimination_singleport'] = discrimination_singleport_iteration

# def probes_iteration(controller, box, events_since_last):
#     """ This function runs int the main loop in probes mode"""
#     # record any events that have happened on the box     
#     events_since_last_names = [event[1] for event in events_since_last]
#     trial_ended = False
#     # examine what events have happened and trigger new ones, depending on box state
#     if controller.task_state == 'waiting_for_trial':
#         if 'song_trigger' in events_since_last_names:
#             box.play_stim(controller.stimsets[controller.current_trial['stimset_idx']], controller.current_trial['stimulus'])
#             controller.current_trial['start_time'] = box.current_time
#             events_since_last.append((box.current_time, 'song_playback', controller.current_trial['stimulus']))
#             if controller.params['withold_response'] is True:
#                 controller.task_state = 'playing_song'
#             else:
#                 controller.task_state = 'waiting_for_response'
                
#     # if song is playing and responses are ignored during song
#     elif controller.task_state == 'playing_song':
#         # if there is a response
#         if 'response_trigger' in events_since_last_names:
#             box.stop_sounds()
#             events_since_last.append((box.current_time, 'response_during_song_playback_haulted'))
#             controller.current_trial['result'] = 'haulted'
#             controller.current_trial['response_time'] = box.current_time
#             trial_ended = True
#         if box.current_time > controller.current_trial['start_time'] + controller.current_trial['stim_length']:
#             controller.task_state = 'waiting_for_response'

#     # if a trial is ongoing then look for responses
#     elif controller.task_state == 'waiting_for_response':
#         if controller.params['withold_response']:
#             timeout_time = controller.current_trial['start_time'] + controller.current_trial['stim_length'] + controller.params['max_trial_length']
#         else:
#             timeout_time = controller.current_trial['start_time'] + controller.params['max_trial_length']
#         # if there is a response
#         if 'response_trigger' in events_since_last_names:
#             event_idx = events_since_last_names.index('response_trigger')
#             controller.current_trial['response_time'] = box.current_time
#             if controller.current_trial['trial_type'] == 'probe':
#                 controller.current_trial['result'] = 'correct'
#                 events_since_last.append((box.current_time, 'probe_trial - no reward'))
#                 trial_ended = True
#             else:
#                 ## if anwser is correct
#                 if  events_since_last[event_idx][2] == controller.current_trial['correct_answer']:
#                     controller.current_trial['result'] = 'correct'
#                     controller.task_state = 'reward'
#                     events_since_last.append((box.current_time, 'reward_start'))
#                     box.feeder_on()
#                 ## otherwise anwser is incorrect 
#                 else:
#                     controller.current_trial['result'] = 'incorrect'
#                     controller.task_state = 'time_out'
#                     events_since_last.append((box.current_time, 'timeout_start'))

       
#         # if no response and trial has timed out
#         elif box.current_time > timeout_time:
#             controller.current_trial['result'] = 'no_response'
#             events_since_last.append((box.current_time, 'no_response'))
#             trial_ended = True

#     # if the box is in time_out state (after an incorrect trial) 
#     elif controller.task_state == 'time_out':
#         if box.current_time > controller.current_trial['response_time'] + controller.params['timeout_period']:
#             events_since_last.append((box.current_time, 'timout_end'))
#             trial_ended = True
#     # if the reward period is over
#     elif controller.task_state == 'reward':
#         if box.current_time > controller.current_trial['response_time'] + controller.params['feed_time']:
#             box.feeder_off()
#             events_since_last.append((box.current_time, 'reward_end'))
#             trial_ended = True
#     return events_since_last, trial_ended
# iterations['probes'] = probes_iteration


def song_only_iteration(controller, box, events_since_last):
    # record any events that have happened on the box     
    events_since_last_names = [event[1] for event in events_since_last]
    trial_ended = False
    # make any initial parameters
    if controller.task_state == 'prepare_trial':
        controller.task_state = 'waiting_for_trial'
    # examine what events have happened and trigger new ones, depending on box state
    if controller.task_state == 'waiting_for_trial':
        if 'song_trigger' in events_since_last_names:
            box.play_stim(controller.stimsets[controller.current_trial['stimset_idx']], controller.current_trial['stimulus'])
            controller.current_trial['start_time'] = box.current_time
            events_since_last.append((box.current_time, 'song_playback', controller.current_trial['stimulus']))
            controller.task_state = 'playing_song'
    elif controller.task_state == 'playing_song':
        if box.current_time > controller.current_trial['start_time'] + controller.current_trial['stim_length']:
            events_since_last.append((box.current_time,'playback_ended'))
            trial_ended = True
    return events_since_last, trial_ended
iterations['song_only'] = song_only_iteration

def song_plus_food_iteration(controller, box, events_since_last):
    # record any events that have happened on the box     
    events_since_last_names = [event[1] for event in events_since_last]
    trial_ended = False
    # make any initial parameters
    if controller.task_state == 'prepare_trial':
        controller.task_state = 'waiting_for_trial'
    # examine what events have happened and trigger new ones, depending on box state
    if controller.task_state == 'waiting_for_trial':
        if 'song_trigger' in events_since_last_names:
            box.play_stim(controller.stimsets[controller.current_trial['stimset_idx']], controller.current_trial['stimulus'])
            controller.current_trial['start_time'] = box.current_time
            events_since_last.append((box.current_time, 'song_playback', controller.current_trial['stimulus']))
            controller.task_state = 'playing_song'
        elif 'response_trigger' in events_since_last_names:
            controller.task_state = 'reward'
            events_since_last.append((box.current_time, 'reward_start'))
            controller.current_trial['start_time'] = box.current_time
            controller.current_trial['response_time'] = box.current_time
            box.feeder_on()
    elif controller.task_state == 'playing_song':
        if box.current_time > controller.current_trial['start_time'] + controller.current_trial['stim_length']:
            events_since_last.append((box.current_time,'playback_ended'))
            trial_ended = True
        if 'response_trigger' in events_since_last_names:
            controller.task_state = 'reward'
            events_since_last.append((box.current_time, 'reward_start'))
            controller.current_trial['response_time'] = box.current_time             
            box.feeder_on()
    # if the reward period is over
    elif controller.task_state == 'reward':
        if box.current_time > controller.current_trial['response_time'] + controller.params['feed_time']:
            # GK
            if box.box_name == 'box_3':
                box.beep_warning()
                time.sleep(1)
            box.feeder_off()
            events_since_last.append((box.current_time, 'reward_end'))
            trial_ended = True
    return events_since_last, trial_ended
iterations['song_plus_food'] = song_plus_food_iteration

def sequence_iteration(controller, box, events_since_last):
    # record any events that have happened on the box     
    events_since_last_names = [event[1] for event in events_since_last]
    trial_ended = False
        # make any initial parameters
    if controller.task_state == 'prepare_trial':
        controller.task_state = 'waiting_for_trial'
    # examine what events have happened and trigger new ones, depending on box state
    if controller.task_state == 'waiting_for_trial':
        if 'song_trigger' in events_since_last_names:
            box.play_stim(controller.stimsets[controller.current_trial['stimset_idx']], controller.current_trial['stimulus'])
            controller.current_trial['start_time'] = box.current_time
            events_since_last.append((box.current_time, 'song_playback', controller.current_trial['stimulus']))
            if controller.params['withold_response'] is True:
                controller.task_state = 'playing_song'
            else:
                controller.task_state = 'waiting_for_response'
    # if song is playing and responses are ignored during song
    elif controller.task_state == 'playing_song':
        # if there is a response
        if 'response_trigger' in events_since_last_names:
            box.stop_sounds()
            events_since_last.append((box.current_time, 'response_during_song_playback_haulted'))
            controller.current_trial['result'] = 'haulted'
            controller.current_trial['response_time'] = box.current_time
            trial_ended = True
        if box.current_time > controller.current_trial['start_time'] + controller.current_trial['stim_length']:
            controller.task_state = 'waiting_for_response'
    # if a trial is ongoing then look for responses
    elif controller.task_state == 'waiting_for_response':
        if controller.params['withold_response']:
            timeout_time = controller.current_trial['start_time'] + controller.current_trial['stim_length'] + controller.params['max_trial_length']
        else:
            timeout_time = controller.current_trial['start_time'] + controller.params['max_trial_length']
        # if there is a response
        if 'response_trigger' in events_since_last_names:
            event_idx = events_since_last_names.index('response_trigger')
            controller.current_trial['response_time'] = box.current_time
            ## if anwser is correct
            controller.current_trial['result'] = 'correct'
            controller.task_state = 'reward'
            events_since_last.append((box.current_time, 'reward_start'))
             
            box.feeder_on()
            ## otherwise anwser is incorrect 
        # if no response and trial has timed out
        elif box.current_time > timeout_time:
            controller.current_trial['result'] = 'no_response'
            events_since_last.append((box.current_time, 'no_response'))
            trial_ended = True
    # if the reward period is over
    elif controller.task_state == 'reward':
        if box.current_time > controller.current_trial['response_time'] + controller.params['feed_time']:
            box.feeder_off()
            events_since_last.append((box.current_time, 'reward_end'))
            trial_ended = True
    return events_since_last, trial_ended
iterations['sequence'] = sequence_iteration


def sequence_singleport_iteration(controller, box, events_since_last):
    # record any events that have happened on the box     
    events_since_last_names = [event[1] for event in events_since_last]
    trial_ended = False
    # make any initial parameters
    if controller.task_state == 'prepare_trial':
        controller.task_state = 'waiting_for_trial'
    # examine what events have happened and trigger new ones, depending on box state
    if controller.task_state == 'waiting_for_trial':
        if 'song_trigger' in events_since_last_names:
            box.play_stim(controller.stimsets[controller.current_trial['stimset_idx']], controller.current_trial['stimulus'])
            controller.current_trial['start_time'] = box.current_time
            events_since_last.append((box.current_time, 'song_playback', controller.current_trial['stimulus']))
            if controller.params['withold_response'] is True:
                controller.task_state = 'playing_song'
            else:
                controller.task_state = 'waiting_for_response'
    # if song is playing and responses are ignored during song
    elif controller.task_state == 'playing_song':
        # if there is a response
        # if 'song_trigger' in events_since_last_names:
        #     box.stop_sounds()
        #     events_since_last.append((box.current_time, 'response_during_song_playback_haulted'))
        #     controller.current_trial['result'] = 'haulted'
        #     controller.current_trial['response_time'] = box.current_time
        #     trial_ended = True
        if box.current_time > controller.current_trial['start_time'] + controller.current_trial['stim_length']:
            controller.task_state = 'waiting_for_response'
    # if a trial is ongoing then look for responses
    elif controller.task_state == 'waiting_for_response':
        if controller.params['withold_response']:
            timeout_time = controller.current_trial['start_time'] + controller.current_trial['stim_length'] + controller.params['max_trial_length']
        else:
            timeout_time = controller.current_trial['start_time'] + controller.params['max_trial_length']
        # if there is a response
        if 'song_trigger' in events_since_last_names:
            # event_idx = events_since_last_names.index('response_trigger')
            controller.current_trial['response_time'] = box.current_time
            ## if anwser is correct
            controller.current_trial['result'] = 'correct'
            controller.task_state = 'reward'
            events_since_last.append((box.current_time, 'reward_start'))
             
            box.feeder_on()
            ## otherwise anwser is incorrect 
        # if no response and trial has timed out
        elif box.current_time > timeout_time:
            controller.current_trial['result'] = 'no_response'
            events_since_last.append((box.current_time, 'no_response'))
            trial_ended = True
    # if the reward period is over
    elif controller.task_state == 'reward':
        if box.current_time > controller.current_trial['response_time'] + controller.params['feed_time']:
            box.feeder_off()
            events_since_last.append((box.current_time, 'reward_end'))
            trial_ended = True
    return events_since_last, trial_ended
iterations['sequence_singleport'] = sequence_singleport_iteration


class DiscriminationStateMachine(object):
    def __init__(self):
        pass
    def waiting_for_trial(self, box, ):
        if 'song_trigger' in events_since_last_names:
            box.play_stim(controller.stimsets[controller.current_trial['stimset_idx']], controller.current_trial['stimulus'])
            controller.current_trial['start_time'] = box.current_time
            events_since_last.append((box.current_time, 'song_playback', controller.current_trial['stimulus']))
            if controller.params['withold_response'] is True:
                controller.task_state = 'playing_song'
            else:
                controller.task_state = 'waiting_for_response'

    def playing_song(self): 
    # if song is playing and responses are ignored during song
        # if there is a response
        if 'response_trigger' in events_since_last_names:
            box.stop_sounds()
            events_since_last.append((box.current_time, 'response_during_song_playback_haulted'))
            controller.current_trial['result'] = 'haulted'
            controller.current_trial['response_time'] = box.current_time
            trial_ended = True
        if box.current_time > controller.current_trial['start_time'] + controller.current_trial['stim_length']:
            controller.task_state = 'waiting_for_response'

    def waiting_for_response(self):
        # if a trial is ongoing then look for responses
        if controller.params['withold_response']:
            timeout_time = controller.current_trial['start_time'] + controller.current_trial['stim_length'] + controller.params['max_trial_length']
        else:
            timeout_time = controller.current_trial['start_time'] + controller.params['max_trial_length']
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
                if controller.params['timeout_light']:
                    box.light_off()
                    events_since_last.append((box.current_time, 'light_off'))
        # if no response and trial has timed out
        elif box.current_time > timeout_time:
            controller.current_trial['result'] = 'no_response'
            events_since_last.append((box.current_time, 'no_response'))
            trial_ended = True
            # if the box is in time_out state (after an incorrect trial) 
    def time_out(self):
        if box.current_time > controller.current_trial['response_time'] + controller.params['timeout_period']:
            box.light_on()
            events_since_last.append((box.current_time, 'timout_end'))
            if controller.params['timeout_light']:
                box.light_on()
                events_since_last.append((box.current_time, 'light_on'))
            trial_ended = True
        # if the reward period is over
    def reward(self):
        if box.current_time > controller.current_trial['response_time'] + controller.params['feed_time']:
            box.feeder_off()
            events_since_last.append((box.current_time, 'reward_end'))
            trial_ended = True
    # return events_since_last, trial_ended


def discrimination_laser_iteration(controller, box, events_since_last):
    """ This function runs int the main loop in discrimination mode"""
    # record any events that have happened on the box     
    events_since_last_names = [event[1] for event in events_since_last]
    trial_ended = False
    # make any initial parameters
    if controller.task_state == 'prepare_trial':
        if 'laser_trial' in controller.current_trial.keys() and controller.current_trial['laser_trial'] == True:
            box.set_pulse_period(controller.current_trial['pulse_period'])
            box.set_pulse_width(controller.current_trial['pulse_width'])
        controller.task_state = 'waiting_for_trial'

    # examine what events have happened and trigger new ones, depending on box state
    if controller.task_state == 'waiting_for_trial':
        if 'song_trigger' in events_since_last_names:
            if 'laser_trial' in controller.current_trial.keys() and controller.current_trial['laser_trial'] == True:
                box.pulse_on()
                events_since_last.append((box.current_time, 'pulse_on'))
            box.play_stim(controller.stimsets[controller.current_trial['stimset_idx']], controller.current_trial['stimulus'])
            controller.current_trial['start_time'] = box.current_time
            events_since_last.append((box.current_time, 'song_playback', controller.current_trial['stimulus']))
            if controller.params['withold_response'] is True:
                controller.task_state = 'playing_song'
            else:
                controller.task_state = 'waiting_for_response'
    # if song is playing and responses are ignored during song
    elif controller.task_state == 'playing_song':
        # if there is a response
        if 'response_trigger' in events_since_last_names:
            box.stop_sounds()
            events_since_last.append((box.current_time, 'response_during_song_playback_haulted'))
            controller.current_trial['result'] = 'haulted'
            controller.current_trial['response_time'] = box.current_time
            trial_ended = True
        if box.current_time > controller.current_trial['start_time'] + controller.current_trial['stim_length']:
            controller.task_state = 'waiting_for_response'
    # if a trial is ongoing then look for responses
    elif controller.task_state == 'waiting_for_response':
        if box.pulse_state!=0 and box.is_playing() is False:
            box.pulse_off()
            events_since_last.append((box.current_time, 'pulse off'))
        if controller.params['withold_response']:
            timeout_time = controller.current_trial['start_time'] + controller.current_trial['stim_length'] + controller.params['max_trial_length']
        else:
            timeout_time = controller.current_trial['start_time'] + controller.params['max_trial_length']

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
                if controller.params['timeout_light']:
                    box.light_off()
                    events_since_last.append((box.current_time, 'light_off'))

        # if no response and trial has timed out
        elif box.current_time > timeout_time:
            controller.current_trial['result'] = 'no_response'
            events_since_last.append((box.current_time, 'no_response'))
            trial_ended = True

    # if the box is in time_out state (after an incorrect trial) 
    elif controller.task_state == 'time_out':
        if box.current_time > controller.current_trial['response_time'] + controller.params['timeout_period']:
            box.light_on()
            events_since_last.append((box.current_time, 'timout_end'))
            if controller.params['timeout_light']:
                box.light_on()
                events_since_last.append((box.current_time, 'light_on'))
            trial_ended = True
    # if the reward period is over
    elif controller.task_state == 'reward':
        if box.current_time > controller.current_trial['response_time'] + controller.params['feed_time']:
            box.feeder_off()
            events_since_last.append((box.current_time, 'reward_end'))
            trial_ended = True
    return events_since_last, trial_ended
iterations['discrimination_laser'] = discrimination_laser_iteration