import scipy as sp
import numpy as np 
import random 
# import behavior_controller 



generators = {}

def standard_generator(controller, trials_per_block=10):
	trial_block = []
	for k in range(0, trials_per_block):
		trial = {}
		stim_list = controller.list_all_stimuli()
		# pick the stimset and the stimulus
		idx = random.randint(0, len(stim_list)-1)
		trial['stimulus'] = stim_list[idx][2]
		trial['stimset_idx'] = stim_list[idx][0]
		trial['stimset'] = controller.stimset_names[trial['stimset_idx']]
		trial['correct_answer'] = controller.expected_responses[stim_list[idx][0]]
		trial['stim_length'] = float(controller.stimsets[stim_list[idx][0]]['stims'][stim_list[idx][1]]['length'])/controller.stimsets[stim_list[idx][0]]['samprate']
		trial_block.append(trial)
	return trial_block
generators['standard'] = standard_generator