import numpy as np
import scipy as sp


# the loop iterations for each mode are loded into th loop dict.  
iterations = {}
def discrimination_iteration(controller, box):
    """ This function runs int the main loop in discrimination mode"""

    # record any events that have happened on the box     
    events_since_last = box.query_events()
    events_since_last_names = [event[1] for event in events_since_last]
    trial_ended = False
    # examine what events have happened and trigger new ones, depending on box state
    if controller.task_state == 'waiting_for_trial':
        if 'song_trigger' in events_since_last_names:
            box.play_stim(controller.stimsets[controller.current_trial['stimset_idx']], controller.current_trial['stimulus'])
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
    return events_since_last, trial_ended
iterations['discrimination'] = discrimination_iteration

def song_only_iteration(controller, box):
    # record any events that have happened on the box     
    events_since_last = box.query_events()
    events_since_last_names = [event[1] for event in events_since_last]
    trial_ended = False
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

def song_plus_food_iteration(controller, box):
    # record any events that have happened on the box     
    events_since_last = box.query_events()
    events_since_last_names = [event[1] for event in events_since_last]
    trial_ended = False
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
        if box.current_time > controller.current_trial['response_time'] + controller.feed_time:
            box.feeder_off()
            events_since_last.append((box.current_time, 'reward_end'))
            trial_ended = True
    return events_since_last, trial_ended
iterations['song_plus_food'] = song_plus_food_iteration

def sequence_iteration(controller, box):
    # record any events that have happened on the box     
    events_since_last = box.query_events()
    events_since_last_names = [event[1] for event in events_since_last]
    trial_ended = False
    # examine what events have happened and trigger new ones, depending on box state
    if controller.task_state == 'waiting_for_trial':
        if 'song_trigger' in events_since_last_names:
            box.play_stim(controller.stimsets[controller.current_trial['stimset_idx']], controller.current_trial['stimulus'])
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
            controller.current_trial['result'] = 'correct'
            controller.task_state = 'reward'
            events_since_last.append((box.current_time, 'reward_start'))
            box.feeder_on()
            ## otherwise anwser is incorrect 
        # if no response and trial has timed out
        elif box.current_time > controller.current_trial['start_time'] + controller.max_trial_length:
            controller.current_trial['result'] = 'no_response'
            events_since_last.append((box.current_time, 'no_response'))
            trial_ended = True
    # if the reward period is over
    elif controller.task_state == 'reward':
        if box.current_time > controller.current_trial['response_time'] + controller.feed_time:
            box.feeder_off()
            events_since_last.append((box.current_time, 'reward_end'))
            trial_ended = True
    return events_since_last, trial_ended
iterations['sequence'] = sequence_iteration