
import time
import datetime
import numpy as np
import scipy as sp
from scipy.signal import welch
import random

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
            if 'trial_type' in controller.current_trial.keys() and controller.current_trial['trial_type'] == 'probe':
                controller.current_trial['result'] = 'correct'
                events_since_last.append((box.current_time, 'probe_trial - no reward'))
                trial_ended = True
            else:
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
            #box.feeder_off()
            box.feeder_off(controller.params['warn_feeder_off']) # GK
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


def tutoring_iteration(controller, box, events_since_last):
    # record any events that have happened on the box
    events_since_last_names = [event[1] for event in events_since_last]
    trial_ended = False
    current_hour = datetime.datetime.now().hour
    # make any initial parameters
    if controller.task_state == 'prepare_trial':
        if current_hour in controller.params['set_times']:
            controller.task_state = 'waiting_for_trial'
    # examine what events have happened and trigger new ones, depending on box state
    if controller.task_state == 'waiting_for_trial' and current_hour in controller.params['set_times']:
        #---------- Playback on, waiting for trigger ----------#
        if 'song_trigger' in events_since_last_names and controller.rewards_per_session[current_hour] < controller.params['allowed_songs_per_session']:
            controller.rewards_per_session[current_hour] += 1
            #---- stop recorder ----#
            box.recorder.stop()
            events_since_last.append((box.current_time,'recording_stopped'))

            #---- play stimulus ----#
            box.play_stim(controller.stimsets[controller.current_trial['stimset_idx']], controller.current_trial['stimulus'])
            controller.current_trial['start_time'] = box.current_time
            events_since_last.append((box.current_time, 'song_playback', controller.current_trial['stimulus']))
            controller.task_state = 'playing_song'
        if controller.rewards_per_session[current_hour] >= controller.params['allowed_songs_per_session']:
            #--------- Session finished. Pause playback until next session ---------#
            controller.task_state = 'playback_pause'
            events_since_last.append((box.current_time, 'playback_paused'))

    elif controller.task_state == 'playing_song':
        #-------- Song currently being played ---------#
        if box.current_time > controller.current_trial['start_time'] + controller.current_trial['stim_length']:
            events_since_last.append((box.current_time,'playback_ended'))
            #trial_ended = True

            #---- begin timeout period ----#
            controller.task_state = "time_out"
            controller.event_time = box.current_time
            events_since_last.append((box.current_time,'begin_timeout'))

            #---- start recorder ----#
            box.recorder.start()
            events_since_last.append((box.current_time,'recording_started'))

    elif controller.task_state == "time_out":
        #-------- In timeout, switch deactivated --------#
        if box.current_time > controller.event_time + controller.params['timeout_period']:
            if current_hour in controller.params['set_times']:
                controller.task_state = 'waiting_for_trial'
                events_since_last.append((box.current_time,'end_timeout'))

    elif controller.task_state == "playback_pause":
        #-------- Session is finished. Waiting for next session ---------#
#        print current_hour
        if not box.recorder.running:
            box.recorder.start()
        if current_hour in controller.params['set_times']:
            if controller.rewards_per_session[current_hour] == 0:
                controller.task_state = "waiting_for_trial"

        time.sleep(2)

    if current_hour == 0:
        #-------- New day, reset reward counts --------#
        for key in controller.rewards_per_session.iterkeys():
            controller.rewards_per_session[key] = 0

    return events_since_last, trial_ended
iterations['tutoring'] = tutoring_iteration

def sound_triggered_playback_iteration(controller, box, events_since_last):
    # record any events that have happened on the box
    events_since_last_names = [event[1] for event in events_since_last]
    events_since_last_times = [event[0] for evnet in events_since_last]
    trial_ended = False
    current_hour = datetime.datetime.now().hour
    
    # make any initial parameters
    
    if controller.task_state == 'prepare_trial':
        if current_hour in controller.params['set_times']:
            controller.task_state = 'waiting_for_trial'
    # examine what events have happened and trigger new ones, depending on box state
    if controller.task_state == 'waiting_for_trial':
        #---------- Intitiate playback, waiting for trigger ----------#
        if 'Audio Recording Started' in events_since_last_names:
            event_time = events_since_last_times[events_since_last_names.index('Audio Recording Started')]
            # audio_data = events_since_last[events_since_last_names.index('Audio Recording Started')][2]
            # f, psd = welch(audio_data, nperseg=1024)
            # entropy = np.log(np.exp(np.mean(np.log(psd)))/np.mean(psd))
            # print('entropy %s' % entropy)

            # psd_mean = np.log(np.mean(psd))
            # print('mean %s' % psd_mean)
            # delay_test = (box.current_time - box.last_stim) > controller.params['delay_time']
            # entropy_test = entropy < controller.params['max_trigger_entropy']
            # power_test = psd_mean > controller.params['min_trigger_power']
            # print delay_test,entropy_test, power_test
                
            #if controller.current_trial['trial_type'] == 'playback' and delay_test and entropy_test and power_test:
            if controller.current_trial['trial_type'] == 'playback':
                #---- play stimulus ----#
                box.play_stim(controller.stimsets[controller.current_trial['stimset_idx']], controller.current_trial['stimulus'])
                controller.current_trial['start_time'] = box.current_time
                #box.last_stim = box.current_time
                events_since_last.append((box.current_time, 'sound_playback', controller.current_trial['stimulus']))
                controller.task_state = 'playing_sound'

            elif controller.current_trial['trial_type'] == 'probe':
                controller.task_state = 'playing_sound'
                events_since_last.append((box.current_time, 'sound_playback_probe'))

    elif controller.task_state == 'playing_sound':
        if controller.current_trial['trial_type'] == 'playback':
            #-------- Sound currently being played ---------#
            
            if 'audio_threshold_crossing' in events_since_last_names:
                event_time = events_since_last_times[events_since_last_names.index('audio_threshold_crossing')]
                audio_data = events_since_last[events_since_last_names.index('audio_threshold_crossing')][2]
                f, psd = welch(audio_data, nperseg=1024)
                entropy = np.log(np.exp(np.mean(np.log(psd)))/np.mean(psd))
                print('entropy %s' % entropy)

                psd_mean = np.log(np.mean(psd))
                print('mean %s' % psd_mean)
                delay_test = (box.current_time - box.last_stim) > controller.params['delay_time']
                entropy_test = entropy < controller.params['max_trigger_entropy']
                power_test = psd_mean > controller.params['min_trigger_power']
                print delay_test,entropy_test, power_test
                
                if delay_test and entropy_test and power_test:
                    box.play_stim(controller.stimsets[controller.current_trial['stimset_idx']], controller.current_trial['stimulus'])
                    box.last_stim = box.current_time
                    events_since_last.append((box.current_time, 'sound_playback', controller.current_trial['stimulus']))
        
        #if 'stop_triggered_audio' in events_since_last_names or (box.last_stim is not None and (box.current_time - box.last_stim) > controller.params['max_stim_limit']):
        if 'stop_triggered_audio' in events_since_last_names:
        #if box.current_time > controller.current_trial['start_time'] + controller.current_trial['stim_length']:
            events_since_last.append((box.current_time,'playback_ended'))

            if 'audio_saved' in events_since_last_names:   
                trial_ended = True
                #---- begin timeout period ----#
                controller.task_state = "time_out"
                controller.event_time = box.current_time
                events_since_last.append((box.current_time,'begin_timeout'))

    elif controller.task_state == "time_out":
        #-------- In timeout, switch deactivated --------#
        
        if box.current_time > (controller.event_time + controller.params['timeout_period']):
            if current_hour in controller.params['set_times']:
                controller.task_state = 'waiting_for_trial'
                events_since_last.append((box.current_time,'end_timeout'))

    return events_since_last, trial_ended
iterations['sound_triggered_playback'] = sound_triggered_playback_iteration

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
            box.feeder_off(controller.params['warn_feeder_off'])
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


def playback_and_count_iteration(controller, box, events_since_last):
    events_since_last_names = [event[1] for event in events_since_last]
    trial_ended = False
    # make any initial parameters
    if controller.task_state == 'prepare_trial':
        controller.task_state = 'waiting_for_trial'
    # if no trial has been initiatied
    if controller.task_state == 'waiting_for_trial':
        box.play_stim(controller.stimsets[controller.current_trial['stimset_idx']], controller.current_trial['stimulus'])
        controller.task_state = 'delay_period'
        events_since_last.append((box.current_time, 'song_playback', controller.current_trial['stimulus']))
        # prepair trial
        controller.current_trial['start_time'] = box.current_time
        controller.current_trial['stimulus_start'] = box.current_time
        controller.current_trial['response_times'] = []
        controller.current_trial['response_triggers'] = []
    # if the state is delay period
    elif controller.task_state == 'delay_period':
        if box.current_time > controller.current_trial['start_time'] + controller.params['delay_time']:
            controller.task_state = 'feed_period'
            if controller.current_trial['stimset_idx'] == 0:
                controller.current_trial['reward'] = 'yes'
                box.feeder_on()
                controller.current_trial['reward_start_time'] = box.current_time
                events_since_last.append((box.current_time, 'reward_start'))
            elif controller.current_trial['stimset_idx'] == 2:
                if len(controller.current_trial['response_times']) > 0:
                    controller.current_trial['reward'] = 'yes'
                    box.feeder_on()
                    controller.current_trial['reward_start_time'] = box.current_time
                    events_since_last.append((box.current_time, 'reward_start'))
                else:
                    controller.current_trial['reward'] = 'no'
            else:
                controller.current_trial['reward'] = 'no'
    # if the state is feed period
    elif controller.task_state == 'feed_period':
        if box.current_time > controller.current_trial['start_time'] + controller.params['feed_time'] + controller.params['delay_time']:
            controller.task_state = 'isi'
            controller.current_trial['reward_end'] = box.current_time
            if controller.current_trial['reward'] == 'yes':
                box.feeder_off()
                events_since_last.append((box.current_time, 'reward_end'))
    # if in interstimulus interval
    elif controller.task_state == 'isi':
        if box.current_time > controller.current_trial['reward_end'] + controller.current_trial['isi']:
            trial_ended = True
    # during all states record all triggers
    if True in ['trigger' in event for event in events_since_last_names]:
        event_idx = ['trigger' in event for event in events_since_last_names].index(True)
        controller.current_trial['response_times'].append(box.current_time-controller.current_trial['start_time'])
        controller.current_trial['response_triggers'].append(events_since_last_names[event_idx])

    return events_since_last, trial_ended
iterations['playback_and_count'] = playback_and_count_iteration


def unrewarded_sequence_preference_assay(controller, box, events_since_last):
    # record any events that have happened on the box
    events_since_last_names = [event[1] for event in events_since_last]
    trial_ended = False
    # make any initial parameters
    if controller.task_state == 'prepare_trial':
        controller.task_state = 'waiting_for_trial'

    if controller.task_state == 'waiting_for_trial':
        if 'song_trigger' in events_since_last_names:
            event_idx = events_since_last_names.index('song_trigger')
            controller.current_trial['start_time'] = box.current_time
            events_since_last.append((box.current_time, 'trial_initiated', controller.current_trial['stimulus']))
            controller.task_state = 'waiting_for_response'
    # examine what events have happened and trigger new ones, depending on box state
    elif controller.task_state == 'waiting_for_response':
        timeout_time = controller.current_trial['start_time'] + controller.params['max_trial_length']
        if 'response_trigger' in events_since_last_names:
            event_idx = events_since_last_names.index('response_trigger')
            controller.current_trial['response_time'] = box.current_time
            if events_since_last[event_idx][2] in controller.expected_responses:
                resp_idx = controller.expected_responses.index(events_since_last[event_idx][2])
            else:
                resp_idx = 100
            if resp_idx < len(controller.stimsets):
                stimset_idx = resp_idx
                stim_list = controller.list_stimuli(stimset_idxs = [stimset_idx])
                # pick the stimset and the stimulus
                idx = random.randint(0, len(stim_list)-1)
                controller.current_trial['response_time'] = box.current_time
                controller.current_trial['response_idx'] = stimset_idx
                controller.current_trial['stimset'] = controller.stimset_names[stimset_idx]
                controller.current_trial['stimset_idx'] = stimset_idx
                controller.current_trial['stimulus'] = stim_list[idx][2]
                controller.current_trial['stim_length'] = float(controller.stimsets[stim_list[idx][0]]['stims'][stim_list[idx][1]]['length'])/controller.stimsets[stim_list[idx][0]]['samprate']
                box.play_stim(controller.stimsets[stimset_idx], controller.current_trial['stimulus'])
                events_since_last.append((box.current_time, 'song_playback', controller.current_trial['stimulus']))
                controller.task_state = 'playing_song'
        elif box.current_time > timeout_time:
            controller.current_trial['result'] = 'no_response'
            events_since_last.append((box.current_time, 'no_response'))
            trial_ended = True

    elif controller.task_state == 'playing_song':
        if box.current_time > controller.current_trial['response_time'] + controller.current_trial['stim_length']:
            events_since_last.append((box.current_time,'playback_ended'))
            trial_ended = True
    return events_since_last, trial_ended
iterations['unrewarded_preference_sequence'] = unrewarded_sequence_preference_assay


def rewarded_sequence_preference_assay(controller, box, events_since_last):
    # record any events that have happened on the box
    events_since_last_names = [event[1] for event in events_since_last]
    trial_ended = False
    # make any initial parameters
    if controller.task_state == 'prepare_trial':
        controller.task_state = 'waiting_for_trial'

    if controller.task_state == 'waiting_for_trial':
        if 'song_trigger' in events_since_last_names:
            event_idx = events_since_last_names.index('song_trigger')
            controller.current_trial['start_time'] = box.current_time
            events_since_last.append((box.current_time, 'trial_initiated', controller.current_trial['stimulus']))
            controller.task_state = 'waiting_for_response'
    # examine what events have happened and trigger new ones, depending on box state
    elif controller.task_state == 'waiting_for_response':
        timeout_time = controller.current_trial['start_time'] + controller.params['max_trial_length']
        if 'response_trigger' in events_since_last_names:
            event_idx = events_since_last_names.index('response_trigger')
            controller.current_trial['response_time'] = box.current_time
            if events_since_last[event_idx][2] in controller.expected_responses:
                resp_idx = controller.expected_responses.index(events_since_last[event_idx][2])
            else:
                resp_idx = 100
            if resp_idx < len(controller.stimsets):
                stimset_idx = resp_idx
                stim_list = controller.list_stimuli(stimset_idxs = [stimset_idx])
                # pick the stimset and the stimulus
                idx = random.randint(0, len(stim_list)-1)
                controller.current_trial['response_time'] = box.current_time
                controller.current_trial['response_idx'] = stimset_idx
                controller.current_trial['stimset'] = controller.stimset_names[stimset_idx]
                controller.current_trial['stimulus'] = stim_list[idx][2]
                controller.current_trial['stim_length'] = float(controller.stimsets[stim_list[idx][0]]['stims'][stim_list[idx][1]]['length'])/controller.stimsets[stim_list[idx][0]]['samprate']
                controller.current_trial['stimset_idx'] = stimset_idx
                box.play_stim(controller.stimsets[stimset_idx], controller.current_trial['stimulus'])
                events_since_last.append((box.current_time, 'song_playback', controller.current_trial['stimulus']))

                # decide whether to do reward
                rand_value = random.uniform(0,1)
                if rand_value <= controller.current_trial['reward_p'][stimset_idx]:
                    controller.task_state = 'reward'
                    box.feeder_on()
                    controller.current_trial['rewarded'] = True
                    events_since_last.append((box.current_time, 'reward_start'))
                else:
                    controller.task_state = 'playing_song'
                    controller.current_trial['rewarded'] = False
                    events_since_last.append((box.current_time, 'no_reward'))
                print controller.current_trial
        elif box.current_time > timeout_time:
            controller.current_trial['result'] = 'no_response'
            events_since_last.append((box.current_time, 'no_response'))
            trial_ended = True

    elif controller.task_state == "reward":
        if box.current_time > controller.current_trial['response_time'] + controller.params['feed_time']:
            #box.feeder_off()
            box.feeder_off(controller.params['warn_feeder_off']) # GK
            events_since_last.append((box.current_time, 'reward_end'))
            trial_ended = True

    elif controller.task_state == 'playing_song':
        if box.current_time > controller.current_trial['response_time'] + controller.current_trial['stim_length']:
            events_since_last.append((box.current_time,'playback_ended'))
            trial_ended = True

    return events_since_last, trial_ended
iterations['rewarded_preference_sequence'] = rewarded_sequence_preference_assay



def video_preference_assay(controller, box, events_since_last):
    center_bin_time = 30
    interstimulus_interval = 10
    nplaybacks_per_side = 10
    intertrial_interval = 300
    # record any events that have happened on the box
    events_since_last_names = [event[1] for event in events_since_last]
    trial_ended = False

    for event_idx,name in enumerate(events_since_last_names):
        if name == 'pos':
            if events_since_last[2] is not None:
                controller.current_trial['track'].append((events_since_last[event_idx][0], events_since_last[event_idx][2]))
                controller.current_trial['current_bin'] = events_since_last[event_idx][3]
        if name == 'enter_bin':
            controller.current_trial['current_bin'] = events_since_last[event_idx][2]
            controller.current_trial['bin_entries'].append(events_since_last[event_idx])


    if controller.task_state == 'prepare_trial':
        controller.current_trial['start_time']=box.current_time
        controller.task_state = 'waiting_to_start_playback'
        events_since_last.append((box.current_time, 'trial_started'))
    elif controller.task_state == 'waiting_to_start_playback':
        if controller.current_trial['current_bin'] ==1:
            if controller.current_trial['last_center_bin_entry_time'] is None:
                controller.current_trial['last_center_bin_entry_time']=box.current_time
            elif box.current_time > controller.current_trial['last_center_bin_entry_time'] + center_bin_time:
                controller.current_trial['playback_start_time'] = box.current_time
                controller.task_state = 'playback'
                events_since_last.append((box.current_time, 'started_playback'))
            else:
                pass
        else:
            controller.current_trial['last_center_bin_entry_time']=None
        pass
    elif controller.task_state == 'playback':
        if len(controller.current_trial['playbacks'])==0:
            box.stop_sounds()
            side_idx = controller.current_trial['start_side']
            stimset_idx = controller.current_trial['stimset_idxs'][side_idx]
            stim_idx = random.randint(0, len(controller.stimsets[stimset_idx]['stims'])-1)
            box.play_stim(controller.stimsets[stimset_idx], controller.stimsets[stimset_idx]['stims'][stim_idx]['name'],side_idx)
            controller.current_trial['playbacks'].append((box.current_time, side_idx, stimset_idx, stim_idx))
            events_since_last.append((box.current_time, 'playback', 'side_%d' % side_idx, 'stimset_%d' % stimset_idx))
        elif box.current_time >= controller.current_trial['playbacks'][-1][0] + interstimulus_interval:
            box.stop_sounds()
            side_idx = int(not controller.current_trial['playbacks'][-1][1])
            stimset_idx = controller.current_trial['stimset_idxs'][side_idx]
            stim_idx = random.randint(0, len(controller.stimsets[stimset_idx]['stims'])-1)
            box.play_stim(controller.stimsets[stimset_idx], controller.stimsets[stimset_idx]['stims'][stim_idx]['name'],side_idx)
            controller.current_trial['playbacks'].append((box.current_time, side_idx, stimset_idx, stim_idx))
            events_since_last.append((box.current_time, 'playback', 'side_%d' % side_idx, 'stimset_%d' % stimset_idx))

        if len(controller.current_trial['playbacks']) >= 2*nplaybacks_per_side:
            controller.current_trial['end_time'] = box.current_time
            controller.task_state = 'intertrial'
            events_since_last.append((box.current_time, 'end_of_trial'))

    elif controller.task_state == 'intertrial':
        if box.current_time >= controller.current_trial['end_time'] + intertrial_interval:
            trial_ended = True
        pass

    return events_since_last, trial_ended
iterations['video_preference_assay'] = video_preference_assay



def interleaved_video_preference_assay(controller, box, events_since_last):
    center_bin_time = controller.params['center_bin_time']
    interstimulus_interval = controller.params['interstimulus_interval']
    nplaybacks_per_side = controller.params['nplaybacks_per_side']
    intertrial_interval = controller.params['intertrial_interval']
    # record any events that have happened on the box
    events_since_last_names = [event[1] for event in events_since_last]
    trial_ended = False

    for event_idx,name in enumerate(events_since_last_names):
        if name == 'pos':
            controller.current_trial['track'].append((events_since_last[event_idx][0], events_since_last[event_idx][2]))
            controller.current_trial['current_bin'] = events_since_last[event_idx][3]
        if name == 'enter_bin':
            controller.current_trial['current_bin'] = events_since_last[event_idx][2]
            controller.current_trial['bin_entries'].append(events_since_last[event_idx])


    if controller.task_state == 'prepare_trial':
        controller.current_trial['start_time']=box.current_time
        controller.task_state = 'waiting_to_start_playback'
        events_since_last.append((box.current_time, 'trial_started'))
    elif controller.task_state == 'waiting_to_start_playback':
        if controller.current_trial['current_bin'] ==1:
            if controller.current_trial['last_center_bin_entry_time'] is None:
                controller.current_trial['last_center_bin_entry_time']=box.current_time
            elif box.current_time > controller.current_trial['last_center_bin_entry_time'] + center_bin_time:
                controller.current_trial['playback_start_time'] = box.current_time
                controller.task_state = 'playback'
                events_since_last.append((box.current_time, 'started_playback'))
                box.start_video_recording()
                box.start_forced_audio_recording()
            else:
                pass
        else:
            controller.current_trial['last_center_bin_entry_time']=None
        pass
    elif controller.task_state == 'playback':
        if len(controller.current_trial['playbacks'])==0:
            box.stop_sounds()
            side_idx = controller.current_trial['start_side']
            stimset_idx = 0
            stim_idx = controller.current_trial['stim_idxs'][side_idx]
            box.play_stim(controller.stimsets[stimset_idx], controller.stimsets[stimset_idx]['stims'][stim_idx]['name'],side_idx)
            controller.current_trial['playbacks'].append((box.current_time, side_idx, stimset_idx, stim_idx))
            events_since_last.append((box.current_time, 'playback', 'side_%d' % side_idx, 'stimset_%d' % stimset_idx,'stim_%d' % stim_idx,controller.stimsets[stimset_idx]['stims'][stim_idx]['name']))
        elif box.current_time >= controller.current_trial['playbacks'][-1][0] + interstimulus_interval:
            box.stop_sounds()
            side_idx = int(not controller.current_trial['playbacks'][-1][1])
            stimset_idx = 0
            stim_idx = controller.current_trial['stim_idxs'][side_idx]
            box.play_stim(controller.stimsets[stimset_idx], controller.stimsets[stimset_idx]['stims'][stim_idx]['name'],side_idx)
            controller.current_trial['playbacks'].append((box.current_time, side_idx, stimset_idx, stim_idx))
            events_since_last.append((box.current_time, 'playback', 'side_%d' % side_idx, 'stimset_%d' % stimset_idx, 'stim_%d' % stim_idx, controller.stimsets[stimset_idx]['stims'][stim_idx]['name']))

        if len(controller.current_trial['playbacks']) >= 2*nplaybacks_per_side:
            controller.current_trial['end_time'] = box.current_time
            controller.task_state = 'intertrial'
            events_since_last.append((box.current_time, 'end_of_trial'))


    elif controller.task_state == 'intertrial':
        if box.current_time >= controller.current_trial['end_time'] + intertrial_interval:
            trial_ended = True
            box.stop_video_recording()
            box.stop_forced_audio_recording()
        pass

    return events_since_last, trial_ended
iterations['interleaved_video_preference_assay'] = interleaved_video_preference_assay


# alternate stims from multiple different stimsets
def interleaved_video_preference_assay_by_stimset(controller, box, events_since_last):
    center_bin_time = controller.params['center_bin_time']
    interstimulus_interval = controller.params['interstimulus_interval']
    nplaybacks_per_side = controller.params['nplaybacks_per_side']
    intertrial_interval = controller.params['intertrial_interval']
    # record any events that have happened on the box
    events_since_last_names = [event[1] for event in events_since_last]
    trial_ended = False

    for event_idx,name in enumerate(events_since_last_names):
        if name == 'pos':
            controller.current_trial['track'].append((events_since_last[event_idx][0], events_since_last[event_idx][2]))
            controller.current_trial['current_bin'] = events_since_last[event_idx][3]
        if name == 'enter_bin':
            controller.current_trial['current_bin'] = events_since_last[event_idx][2]
            controller.current_trial['bin_entries'].append(events_since_last[event_idx])


    if controller.task_state == 'prepare_trial':
        controller.current_trial['start_time']=box.current_time
        controller.task_state = 'waiting_to_start_playback'
        events_since_last.append((box.current_time, 'trial_started'))
    elif controller.task_state == 'waiting_to_start_playback':
        if controller.current_trial['current_bin'] ==1:
            if controller.current_trial['last_center_bin_entry_time'] is None:
                controller.current_trial['last_center_bin_entry_time']=box.current_time
            elif box.current_time > controller.current_trial['last_center_bin_entry_time'] + center_bin_time:
                controller.current_trial['playback_start_time'] = box.current_time
                controller.task_state = 'playback'
                events_since_last.append((box.current_time, 'started_playback'))
                box.start_video_recording()
                box.start_forced_audio_recording()
            else:
                pass
        else:
            controller.current_trial['last_center_bin_entry_time']=None
        pass
    elif controller.task_state == 'playback':
        if len(controller.current_trial['playbacks'])==0:
            box.stop_sounds()
            side_idx = controller.current_trial['start_side']
            stimset_idx = controller.current_trial['stimset_idxs'][side_idx]
            # stimset_idx= controller.current_trial['stimset_idxs']
            stim_idx = controller.current_trial['stim_idxs'][side_idx]
            box.play_stim(controller.stimsets[stimset_idx], controller.stimsets[stimset_idx]['stims'][stim_idx]['name'],side_idx)
            controller.current_trial['playbacks'].append((box.current_time, side_idx, stimset_idx, stim_idx))
            events_since_last.append((box.current_time, 'playback', 'side_%d' % side_idx, 'stimset_%d' % stimset_idx,'stim_%d' % stim_idx,controller.stimsets[stimset_idx]['stims'][stim_idx]['name']))
        elif box.current_time >= controller.current_trial['playbacks'][-1][0] + interstimulus_interval:
            box.stop_sounds()
            side_idx = int(not controller.current_trial['playbacks'][-1][1])
            stimset_idx = controller.current_trial['stimset_idxs'][side_idx]
            stim_idx = controller.current_trial['stim_idxs'][side_idx]
            box.play_stim(controller.stimsets[stimset_idx], controller.stimsets[stimset_idx]['stims'][stim_idx]['name'],side_idx)
            controller.current_trial['playbacks'].append((box.current_time, side_idx, stimset_idx, stim_idx))
            events_since_last.append((box.current_time, 'playback', 'side_%d' % side_idx, 'stimset_%d' % stimset_idx, 'stim_%d' % stim_idx, controller.stimsets[stimset_idx]['stims'][stim_idx]['name']))

        if len(controller.current_trial['playbacks']) >= 2*nplaybacks_per_side:
            controller.current_trial['end_time'] = box.current_time
            controller.task_state = 'intertrial'
            events_since_last.append((box.current_time, 'end_of_trial'))


    elif controller.task_state == 'intertrial':
        if box.current_time >= controller.current_trial['end_time'] + intertrial_interval:
            trial_ended = True
            box.stop_video_recording()
            box.stop_forced_audio_recording()
        pass

    return events_since_last, trial_ended
iterations['interleaved_video_preference_assay_by_stimset'] = interleaved_video_preference_assay_by_stimset


def interleaved_video_preference_assay_triggered(controller, box, events_since_last):
    center_bin_time = 30
    interstimulus_interval = 10
    nplaybacks_per_side = 10
    intertrial_interval = 500
    # record any events that have happened on the box
    events_since_last_names = [event[1] for event in events_since_last]
    trial_ended = False

    for event_idx,name in enumerate(events_since_last_names):
        if name == 'pos':
            controller.current_trial['track'].append((events_since_last[event_idx][0], events_since_last[event_idx][2]))
            controller.current_trial['current_bin'] = events_since_last[event_idx][3]
        if name == 'enter_bin':
            controller.current_trial['current_bin'] = events_since_last[event_idx][2]
            controller.current_trial['bin_entries'].append(events_since_last[event_idx])


    if controller.task_state == 'prepare_trial':
        controller.current_trial['start_time']=box.current_time
        controller.task_state = 'waiting_to_start_playback'
        events_since_last.append((box.current_time, 'trial_started'))
    elif controller.task_state == 'waiting_to_start_playback':
        if controller.current_trial['current_bin'] ==1:
            if controller.current_trial['last_center_bin_entry_time'] is None:
                controller.current_trial['last_center_bin_entry_time']=box.current_time
            elif box.current_time > controller.current_trial['last_center_bin_entry_time'] + center_bin_time:
                if 'trial_trigger' in events_since_last_names:
                    controller.current_trial['playback_start_time'] = box.current_time
                    controller.task_state = 'playback'
                    events_since_last.append((box.current_time, 'started_playback'))
            else:
                pass
        else:
            controller.current_trial['last_center_bin_entry_time']=None
        pass
    elif controller.task_state == 'playback':
        if len(controller.current_trial['playbacks'])==0:
            box.stop_sounds()
            side_idx = controller.current_trial['start_side']
            stimset_idx = 0
            stim_idx = controller.current_trial['stim_idxs'][side_idx]
            box.play_stim(controller.stimsets[stimset_idx], controller.stimsets[stimset_idx]['stims'][stim_idx]['name'],side_idx)
            controller.current_trial['playbacks'].append((box.current_time, side_idx, stimset_idx, stim_idx))
            events_since_last.append((box.current_time, 'playback', 'side_%d' % side_idx, 'stimset_%d' % stimset_idx,'stim_%d' % stim_idx,controller.stimsets[stimset_idx]['stims'][stim_idx]['name']))
        elif box.current_time >= controller.current_trial['playbacks'][-1][0] + interstimulus_interval:
            box.stop_sounds()
            side_idx = int(not controller.current_trial['playbacks'][-1][1])
            stimset_idx = 0
            stim_idx = controller.current_trial['stim_idxs'][side_idx]
            box.play_stim(controller.stimsets[stimset_idx], controller.stimsets[stimset_idx]['stims'][stim_idx]['name'],side_idx)
            controller.current_trial['playbacks'].append((box.current_time, side_idx, stimset_idx, stim_idx))
            events_since_last.append((box.current_time, 'playback', 'side_%d' % side_idx, 'stimset_%d' % stimset_idx, 'stim_%d' % stim_idx, controller.stimsets[stimset_idx]['stims'][stim_idx]['name']))

        if len(controller.current_trial['playbacks']) >= 2*nplaybacks_per_side:
            controller.current_trial['end_time'] = box.current_time
            controller.task_state = 'intertrial'
            events_since_last.append((box.current_time, 'end_of_trial'))

    elif controller.task_state == 'intertrial':
        if box.current_time >= controller.current_trial['end_time'] + intertrial_interval:
            trial_ended = True
        pass

    return events_since_last, trial_ended
iterations['interleaved_video_preference_assay_triggered'] = interleaved_video_preference_assay_triggered




def interleaved_video_preference_assay_videoplayback(controller, box, events_since_last):
    center_bin_time = 30
    interstimulus_interval = 10
    nplaybacks_per_side = 10
    intertrial_interval = 500
    # record any events that have happened on the box
    events_since_last_names = [event[1] for event in events_since_last]
    trial_ended = False

    for event_idx,name in enumerate(events_since_last_names):
        if name == 'pos':
            controller.current_trial['track'].append((events_since_last[event_idx][0], events_since_last[event_idx][2]))
            controller.current_trial['current_bin'] = events_since_last[event_idx][3]
        if name == 'enter_bin':
            controller.current_trial['current_bin'] = events_since_last[event_idx][2]
            controller.current_trial['bin_entries'].append(events_since_last[event_idx])


    if controller.task_state == 'prepare_trial':
        controller.current_trial['start_time']=box.current_time
        controller.task_state = 'waiting_to_start_playback'
        events_since_last.append((box.current_time, 'trial_started'))
    elif controller.task_state == 'waiting_to_start_playback':
        if controller.current_trial['current_bin'] ==1:
            if controller.current_trial['last_center_bin_entry_time'] is None:
                controller.current_trial['last_center_bin_entry_time']=box.current_time
            elif box.current_time > controller.current_trial['last_center_bin_entry_time'] + center_bin_time:
                controller.current_trial['playback_start_time'] = box.current_time
                controller.task_state = 'playback'
                events_since_last.append((box.current_time, 'started_playback'))
            else:
                pass
        else:
            controller.current_trial['last_center_bin_entry_time']=None
        pass
    elif controller.task_state == 'playback':
        if len(controller.current_trial['playbacks'])==0:
            box.stop_sounds()
            side_idx = controller.current_trial['start_side']
            stimset_idx = 0
            stim_idx = controller.current_trial['stim_idxs'][side_idx]
            box.play_stim(controller.stimsets[stimset_idx], controller.stimsets[stimset_idx]['stims'][stim_idx]['name'],side_idx)
            box.select_screen(side_idx)
            box.play_video('video/Singing4_vertical.mp4')
            controller.current_trial['playbacks'].append((box.current_time, side_idx, stimset_idx, stim_idx))
            events_since_last.append((box.current_time, 'playback', 'side_%d' % side_idx, 'stimset_%d' % stimset_idx,'stim_%d' % stim_idx,controller.stimsets[stimset_idx]['stims'][stim_idx]['name']))
        elif box.current_time >= controller.current_trial['playbacks'][-1][0] + interstimulus_interval:
            box.stop_sounds()
            side_idx = int(not controller.current_trial['playbacks'][-1][1])
            stimset_idx = 0
            stim_idx = controller.current_trial['stim_idxs'][side_idx]
            box.play_stim(controller.stimsets[stimset_idx], controller.stimsets[stimset_idx]['stims'][stim_idx]['name'],side_idx)
            box.select_screen(side_idx)
            box.play_video('video/Singing4_vertical.mp4')
            controller.current_trial['playbacks'].append((box.current_time, side_idx, stimset_idx, stim_idx))
            events_since_last.append((box.current_time, 'playback', 'side_%d' % side_idx, 'stimset_%d' % stimset_idx, 'stim_%d' % stim_idx, controller.stimsets[stimset_idx]['stims'][stim_idx]['name']))

        if len(controller.current_trial['playbacks']) >= 2*nplaybacks_per_side:
            controller.current_trial['end_time'] = box.current_time
            controller.task_state = 'intertrial'
            events_since_last.append((box.current_time, 'end_of_trial'))

    elif controller.task_state == 'intertrial':
        if box.current_time >= controller.current_trial['end_time'] + intertrial_interval:
            trial_ended = True
        pass

    return events_since_last, trial_ended
iterations['interleaved_video_preference_assay_videoplayback'] = interleaved_video_preference_assay_videoplayback
