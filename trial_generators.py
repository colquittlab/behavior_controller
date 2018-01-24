import scipy as sp
import numpy as np 
import random 
"""
task specific generators are defined here and loaded into the library generators.  This is hand spun and the convention is genorators['name']=name_generator
"""

generators = {}


def standard_generator(controller, trials_per_block=1):
	"""Generates trial by trial with no pruning"""
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
generators['standard'] = standard_generator



def video_preference_generator(controller, trials_per_block=1):
	"""Generates trial by trial with no pruning"""
	trial_block = []
	for k in range(0, trials_per_block):
		trial = {}
		# pick the stimset and the stimulus
		# idx = random.randint(0, 1)
		# if idx == 0:
		# 	trial['stimset_idxs'] = [0, 1]
		# else:
		# 	trial['stimset_idxs'] = [1, 0]
		trial['stimset_idxs'] = [0, 1] # have the same stimset on each side
		trial['start_side'] = random.randint(0,1)
		trial['current_bin'] = None
		trial['track'] = []
		trial['bin_entries'] = []
		trial['last_center_bin_entry_time']=None
		trial['trial_type'] = 'video_preference'
		trial['playbacks'] = []
		trial_block.append(trial)
	return trial_block
generators['video_preference'] = video_preference_generator

def interleaved_video_preference_generator(controller, trials_per_block=1):
	"""Generates trial by trial with no pruning"""
	trial_block = []
	for k in range(0, trials_per_block):
		trial = {}
		# pick the stimset and the stimulus
		trial['stimset_idxs'] = [0]
		trial['stim_idxs'] = random.sample(range(0,len(controller.stimsets[0]['stims'])),2)
		trial['start_side'] = random.randint(0,1)
		trial['current_bin'] = None
		trial['track'] = []
		trial['bin_entries'] = []
		trial['last_center_bin_entry_time']=None
		trial['trial_type'] = 'video_preference'
		trial['playbacks'] = []
		trial_block.append(trial)
	return trial_block
generators['interleaved_video_preference'] = interleaved_video_preference_generator


def interleaved_video_preference_generator_by_stimset(controller, trials_per_block=1):
	"""Generates trial by trial with no pruning"""
	trial_block = []
	for k in range(0, trials_per_block):
		trial = {}
		# pick the stimset and the stimulus
		# pick the stimset and the stimulus
		trial['stimset_idxs'] = random.sample(range(0,len(controller.stimsets)),2)
		# trial['stimset_idxs'] = [1]
		trial['stim_idxs'] = []
		for stimset in trial['stimset_idxs']:
			trial['stim_idxs'].append(random.sample(range(0,len(controller.stimsets[stimset]['stims'])),1)[0])
		# trial['stim_idxs'] = random.sample(range(0,len(controller.stimsets[0]['stims'])),2)
		trial['start_side'] = random.randint(0,1)
		trial['current_bin'] = None
		trial['track'] = []
		trial['bin_entries'] = []
		trial['last_center_bin_entry_time']=None
		trial['trial_type'] = 'video_preference'
		trial['playbacks'] = []
		trial_block.append(trial)
	return trial_block
generators['interleaved_video_preference_by_stimset'] = interleaved_video_preference_generator_by_stimset


def preference_generator(controller, trials_per_block=1):
	"""Generates trial by trial with no pruning"""
	trial_block = []
	for k in range(0, trials_per_block):
		trial = {}
		trial['trial_type'] = 'preference'
		trial['reward_p'] = [1]*len(controller.stimsets)
		trial['stimulus']=''
		# pick the stimset and the stimulus
		trial_block.append(trial)
	return trial_block
generators['preference'] = preference_generator




def adaptive_preference_generator(controller, trials_per_block=1, n_trials_back=10):
	"""Generates trial by trial with no pruning"""
	trial_block = []
	for k in range(0, trials_per_block):
		trial = {}
		trial['trial_type'] = 'preference'
		trial['reward_p'] = [1]*len(controller.stimsets)
		trial['stimulus']=''
		if len(controller.completed_trials)>=n_trials_back:
			stats = controller.calculate_performance_statistics(n_trials_back = n_trials_back)
			for stimset_idx in range(0,len(controller.stimsets)):
				bias = np.max([stats['by_stimset'][stimset_idx]['p_occurance']-0.5, 0])
				p0 = 0.75
				trial['reward_p'][stimset_idx] = p0 - p0*2*bias
			# import ipdb; ipdb.set_trace()
			print stats

		# pick the stimset and the stimulus
		trial_block.append(trial)
	return trial_block
generators['adaptive_preference'] = adaptive_preference_generator


def stimset_occurance_generator(controller, trials_per_block=1):
	"""Generates trial by trial with no pruning but allows you to set stimet occurance"""
	trial_block = []
	if sum(controller.params['stimset_occurance']) != 1:
		raise Exception('Stimset Occurance does not sum to 1')


	for k in range(0, trials_per_block):
		trial = {}
		if random.uniform(0,1) < float(controller.params['probe_occurance']) / 100:
			trial['trial_type'] = 'probe'
			stim_list = controller.list_stimuli(stimset_idxs = [2])
		else:
			trial['trial_type'] = 'discrimination'
			stim_list = controller.list_stimuli(stimset_idxs = [0, 1])
			rand_num = random.uniform(0,1)
			for stimset_idx in range(0,len(controller.params['stimset_occurance'])):
				if rand_num < sum(controller.params['stimset_occurance'][:stimset_idx+1]):
					break
			stim_list = controller.list_stimuli(stimset_idxs = [stimset_idx])
		
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
generators['stimset_occurance'] = stimset_occurance_generator

# def standard_playback_generator(controller, trials_per_block=1):
# 	"""Generates trial by trial with no pruning"""
# 	trial_block = []
# 	for k in range(0, trials_per_block):
# 		trial = {}
# 		# pick the stimset and the stimulus
# 		stim_list = controller.list_stimuli(stimset_idxs = [0, 1])
# 		idx = random.randint(0, len(stim_list)-1)
# 		trial['stimulus'] = stim_list[idx][2]
# 		trial['stimset_idx'] = stim_list[idx][0]
# 		trial['stimset'] = controller.stimset_names[trial['stimset_idx']]
# 		trial['stim_length'] = float(controller.stimsets[stim_list[idx][0]]['stims'][stim_list[idx][1]]['length'])/controller.stimsets[stim_list[idx][0]]['samprate']
# 		if controller.params['isi_distribution'] == 'exponential':
# 			trial['isi'] = np.random.exponential(controller.params['isi_parameter'])
# 		elif controller.params['isi_distribution'] == 'uniform':
# 			trial['isi']  = np.random.uniform(controller.params['isi_parameter'][0],controller.params['isi_parameter'][1])
# 		elif controller.params['isi_distribution'] == 'fixed':
# 			trial['isi'] = controller.params['isi_parameter']
# 		trial_block.append(trial)
# 	return trial_block
# generators['standard_playback'] = standard_playback_generator

def playback_generator(controller, trials_per_block=1):
	"""Generates trial by trial with no pruning but allows you to set stimet occurance"""
	trial_block = []
	if sum(controller.params['stimset_occurance']) != 1:
		raise Exception('Stimset Occurance does not sum to 1')

	for k in range(0, trials_per_block):
		trial = {}
		if random.uniform(0,1) < float(controller.params['probe_occurance']) / 100:
			trial['trial_type'] = 'probe'
			stim_list = controller.list_stimuli(stimset_idxs = [2])
		else:
			trial['trial_type'] = 'discrimination'
			stim_list = controller.list_stimuli(stimset_idxs = [0, 1])
			rand_num = random.uniform(0,1)
			for stimset_idx in range(0,len(controller.params['stimset_occurance'])):
				if rand_num < sum(controller.params['stimset_occurance'][:stimset_idx+1]):
					break
			stim_list = controller.list_stimuli(stimset_idxs = [stimset_idx])
		
		# pick the stimset and the stimulus
		idx = random.randint(0, len(stim_list)-1)
		trial['stimulus'] = stim_list[idx][2]
		trial['stimset_idx'] = stim_list[idx][0]
		trial['stimset'] = controller.stimset_names[trial['stimset_idx']]
		trial['stim_length'] = float(controller.stimsets[stim_list[idx][0]]['stims'][stim_list[idx][1]]['length'])/controller.stimsets[stim_list[idx][0]]['samprate']
		if controller.params['isi_distribution'] == 'exponential':
			trial['isi'] = np.random.exponential(controller.params['isi_parameter'])
		elif controller.params['isi_distribution'] == 'uniform':
			trial['isi']  = np.random.uniform(controller.params['isi_parameter'][0],controller.params['isi_parameter'][1])
		elif controller.params['isi_distribution'] == 'fixed':
			trial['isi'] = controller.params['isi_parameter']
		trial_block.append(trial)
	return trial_block
generators['playback'] = playback_generator


def gk_without_replacement_generator(controller, trials_per_block=None):
	"""Generate a block of trials the size of all stimuli and sample without replacement"""
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


def gk_without_replacement_adaptive_generator(controller, trials_per_block=None):
	"""Generate a block of trials the size  of all stimuli and sample without replacement.
	Then prune the block based on gk's (kn's) adaptive algorithm"""
	trial_block = []
	if sum(controller.params['stimset_occurance']) != 1:
		raise Exception('Stimset Occurance does not sum to 1')	
	
	if len(controller.completed_trials) == 0:
		if len(controller.params['stimset_occurance']) > 0:
			controller.Aocc = controller.params['stimset_occurance'][0]
			controller.Bocc = controller.params['stimset_occurance'][1]
			print 'Aocc=',controller.Aocc,' Bocc=',controller.Bocc

	if len(controller.completed_trials) > 40:
		stats = controller.calculate_performance_statistics(n_trials_back = 40)
		print 'A_n_correct+n_incorrect=',stats['by_stimset'][0]['n_correct']+stats['by_stimset'][0]['n_incorrect']
		print 'B_n_correct+n_incorrect=',stats['by_stimset'][1]['n_correct']+stats['by_stimset'][1]['n_incorrect']
		if (stats['by_stimset'][0]['n_correct']+stats['by_stimset'][0]['n_incorrect']) >= 5 and (stats['by_stimset'][1]['n_correct']+stats['by_stimset'][1]['n_incorrect']) >= 5:
			if stats['by_stimset'][1]['p_correct'] + stats['by_stimset'][0]['p_correct'] != 0:
				controller.Aocc = stats['by_stimset'][1]['p_correct']/(stats['by_stimset'][1]['p_correct'] + stats['by_stimset'][0]['p_correct'])
				controller.Bocc = 1 - controller.Aocc
				print 'Aocc=',controller.Aocc,' Bocc=',controller.Bocc
	
	print 'len(controller.completed_trials)=',len(controller.completed_trials)
	print 'Aocc=',controller.Aocc,' Bocc=',controller.Bocc

	A_stimuli = controller.list_stimuli(stimset_idxs = [0])
	B_stimuli = controller.list_stimuli(stimset_idxs = [1])
	if controller.Aocc < 0.5:
		random.shuffle(A_stimuli)
		nsubtract = int(round((len(A_stimuli)-controller.Aocc*(len(A_stimuli)+len(B_stimuli))) / (1-controller.Aocc) ))
		if nsubtract == len(A_stimuli):
			A_stimuli = [A_stimuli[0]]
		else:
			A_stimuli = A_stimuli[:len(A_stimuli)-nsubtract]
	if controller.Bocc < 0.5:				
		random.shuffle(B_stimuli)
		nsubtract = int(round((len(B_stimuli)-controller.Bocc*(len(A_stimuli)+len(B_stimuli))) / (1-controller.Bocc) ))
		if nsubtract == len(B_stimuli):
			B_stimuli = [B_stimuli[0]]
		else:
			B_stimuli = B_stimuli[:len(B_stimuli)-nsubtract]
		
	print 'nAstim=',len(A_stimuli),' nBstim=',len(B_stimuli) 

	stim_list = []
	stim_list.extend(A_stimuli)
	stim_list.extend(B_stimuli)
	trials_per_block = len(stim_list)
	idx_list = random.sample(xrange(0, len(stim_list)), len(stim_list))
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
generators['gk_without_replacement_adaptive'] = gk_without_replacement_adaptive_generator



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
	"""Fights perch bias adaptively as in gk_without_replacement_adaptive"""
	trial_block = []
	if sum(controller.params['stimset_occurance']) != 1:
		raise Exception('Stimset Occurance does not sum to 1')	
	
	print 'n_completed_trials=',len(controller.completed_trials)

	if len(controller.completed_trials) > 25:
		print 1
		stats = controller.calculate_performance_statistics(n_trials_back = 25)
		if (stats['by_stimset'][0]['n_correct']+stats['by_stimset'][0]['n_incorrect']) >= 10 and (stats['by_stimset'][1]['n_correct']+stats['by_stimset'][1]['n_incorrect']) >= 10:
			if stats['by_stimset'][1]['p_correct'] + stats['by_stimset'][0]['p_correct'] == 0:
				print 2
				Aocc = controller.params['stimset_occurance'][0]
				Bocc = controller.params['stimset_occurance'][1]				
			else:
				print 3
				Aocc = stats['by_stimset'][1]['p_correct']/(stats['by_stimset'][1]['p_correct'] + stats['by_stimset'][0]['p_correct'])
				Bocc = 1 - Aocc

				print 'n_correctA=',stats['by_stimset'][0]['n_correct']
				print 'n_incorrectA=',stats['by_stimset'][0]['n_incorrect']
				print 'n_correctB=',stats['by_stimset'][1]['n_correct']
				print 'n_incorrectB=',stats['by_stimset'][1]['n_incorrect']
				print 'pA=',stats['by_stimset'][0]['p_correct']
				print 'pB=',stats['by_stimset'][1]['p_correct']
				print 'Aocc=',Aocc,' Bocc=',Bocc
		else:
			Aocc = controller.params['stimset_occurance'][0]
			Bocc = controller.params['stimset_occurance'][1]
	else:
		print 4
		Aocc = controller.params['stimset_occurance'][0]
		Bocc = controller.params['stimset_occurance'][1]
		print 'Aocc=',Aocc,' Bocc=',Bocc
		
	A_stimuli = controller.list_stimuli(stimset_idxs = [0])
	B_stimuli = controller.list_stimuli(stimset_idxs = [1])
	if Aocc < 0.5:
		print 5
		random.shuffle(A_stimuli)
		nsubtract = int(round((len(A_stimuli) - Aocc*(len(A_stimuli)+len(B_stimuli))) / (1-Aocc) ))
		A_stimuli = A_stimuli[:len(A_stimuli)-nsubtract]
	if Bocc < 0.5:
		print 6				
		random.shuffle(B_stimuli)
		nsubtract = int(round((len(B_stimuli) - Bocc*(len(A_stimuli)+len(B_stimuli))) / (1-Bocc) ))
		B_stimuli = B_stimuli[:len(B_stimuli)-nsubtract]
		
	stim_list = []
	stim_list.extend(A_stimuli)
	stim_list.extend(B_stimuli)		
	trials_per_block = len(stim_list)
	idx_list = random.sample(xrange(0, len(stim_list)), len(stim_list))
	#print idx_list

	for k in range(0, trials_per_block):
		trial = {}
		#stim_list = controller.list_stimuli()
		# pick the stimset and the stimulus
		idx = idx_list[k]

		#print stim_list[idx][2].split('_')[-1]

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
