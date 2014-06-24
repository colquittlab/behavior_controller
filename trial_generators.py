import scipy as sp
import numpy as np 
import random 


generators = {}


def standard_generator(controller, trials_per_block=1):
	"""Generates trial by trial with no pruning"""
	trial_block = []
	for k in range(0, trials_per_block):
		trial = {}
		stim_list = controller.list_stimuli()
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


def stimset_occurance_generator(controller, trials_per_block=1):
	"""Generates trial by trial with no pruning"""
	trial_block = []
	if sum(controller.params['stimset_occurance']) != 1:
		raise Exception('Stimset Occurance does not sum to 1')

	for k in range(0, trials_per_block):
		rand_num = random.uniform(0,1)
		for stimset_idx in range(0,len(controller.params['stimset_occurance'])):
			if rand_num < sum(controller.params['stimset_occurance'][:stimset_idx+1]):
				break

		trial = {}
		stim_list = controller.list_stimuli(stimset_idxs = [stimset_idx])
		# pick the stimset and the stimulus
		idx = random.randint(0, len(stim_list)-1)

		trial['stimulus'] = stim_list[idx][2]
		trial['stimset_idx'] = stim_list[idx][0]
		trial['stimset'] = controller.stimset_names[trial['stimset_idx']]
		trial['correct_answer'] = controller.expected_responses[stim_list[idx][0]]
		trial['stim_length'] = float(controller.stimsets[stim_list[idx][0]]['stims'][stim_list[idx][1]]['length'])/controller.stimsets[stim_list[idx][0]]['samprate']
		trial_block.append(trial)
	return trial_block
generators['stimset_occurance'] = stimset_occurance_generator

def gk_without_replacement_generator(controller, trials_per_block=None):
	"""Generate a block of trials the size  of all stimuli and sample without replacement"""
	trial_block = []
	stim_list = controller.list_stimuli()
	trials_per_block = len(stim_list)
	idx_list = random.sample(xrange(0, len(stim_list)), len(stim_list))
	#print idx_list

	for k in range(0, trials_per_block):
		trial = {}
		#stim_list = controller.list_stimuli()
		# pick the stimset and the stimulus
		idx = idx_list[k]

		trial['stimulus'] = stim_list[idx][2]
		trial['stimset_idx'] = stim_list[idx][0]
		trial['stimset'] = controller.stimset_names[trial['stimset_idx']]
		trial['correct_answer'] = controller.expected_responses[stim_list[idx][0]]
		trial['stim_length'] = float(controller.stimsets[stim_list[idx][0]]['stims'][stim_list[idx][1]]['length'])/controller.stimsets[stim_list[idx][0]]['samprate']
		trial_block.append(trial)
	return trial_block
generators['gk_without_replacement'] = gk_without_replacement_generator



def standard_laser_generator(controller, trials_per_block=1):
	"""Generates trial by trial with no pruning"""
	trial_block = []
	for k in range(0, trials_per_block):
		trial = {}
		stim_list = controller.list_stimuli()
		# pick the stimset and the stimulus
		idx = random.randint(0, len(stim_list)-1)

		trial['stimulus'] = stim_list[idx][2]
		trial['stimset_idx'] = stim_list[idx][0]
		trial['stimset'] = controller.stimset_names[trial['stimset_idx']]
		trial['correct_answer'] = controller.expected_responses[stim_list[idx][0]]
		trial['stim_length'] = float(controller.stimsets[stim_list[idx][0]]['stims'][stim_list[idx][1]]['length'])/controller.stimsets[stim_list[idx][0]]['samprate']
		
		if random.uniform(0,1) < float(controller.params['laser_occurance'])/100:
			trial['laser_trial'] = True
			trial['pulse_width'] = controller.params['pulse_width']
			trial['pulse_period'] = controller.params['pulse_period']
		else:
			trial['laser_trial'] = False
		trial_block.append(trial)
	return trial_block
generators['standard_laser'] = standard_laser_generator

def gk_labeled_laser_without_replacement_generator(controller, trials_per_block=None):
	"""Generate a block of trials the size  of all stimuli and sample without replacement"""
	"""Triggers laser for stimuli with 'laseron' at the end of the name"""
	trial_block = []
	stim_list = controller.list_stimuli()
	trials_per_block = len(stim_list)
	idx_list = random.sample(xrange(0, len(stim_list)), len(stim_list))
	#print idx_list

	for k in range(0, trials_per_block):
		trial = {}
		#stim_list = controller.list_stimuli()
		# pick the stimset and the stimulus
		idx = idx_list[k]

		if stim_list[idx][2].split('_')[-1] == 'laseron':
			trial['laser_trial'] = True
			trial['pulse_width'] = controller.params['pulse_width']
			trial['pulse_period'] = controller.params['pulse_period']
		else:
			trial['laser_trial'] = False

		trial['stimulus'] = stim_list[idx][2]
		trial['stimset_idx'] = stim_list[idx][0]
		trial['stimset'] = controller.stimset_names[trial['stimset_idx']]
		trial['correct_answer'] = controller.expected_responses[stim_list[idx][0]]
		trial['stim_length'] = float(controller.stimsets[stim_list[idx][0]]['stims'][stim_list[idx][1]]['length'])/controller.stimsets[stim_list[idx][0]]['samprate']
		trial_block.append(trial)
	return trial_block
generators['gk_labeled_laser_without_replacement'] = gk_labeled_laser_without_replacement_generator


def probes_generator(controller, trials_per_block=100):
	trial_block = []
	for k in range(0, trials_per_block):
		trial = {}

		if random.uniform(0,1) < float(controller.params['probe_occurance']) / 100:
			trial['trial_type'] = 'probe'
			stim_list = controller.list_stimuli(stimset_idxs = [2])
		else:
			trial['trial_type'] = 'discrimination'
			stim_list = controller.list_stimuli(stimset_idxs = [0, 1])

		# pick the stimset and the stimulus
		idx = random.randint(0, len(stim_list)-1)
		trial['stimulus'] = stim_list[idx][2]
		trial['stimset_idx'] = stim_list[idx][0]
		trial['stimset'] = controller.stimset_names[trial['stimset_idx']]
		trial['stim_length'] = float(controller.stimsets[stim_list[idx][0]]['stims'][stim_list[idx][1]]['length'])/controller.stimsets[stim_list[idx][0]]['samprate']
		if trial['trial_type'] == 'discrimination':
			trial['correct_answer'] = controller.expected_responses[stim_list[idx][0]]
		trial_block.append(trial)
	return trial_block
generators['probes'] = probes_generator
