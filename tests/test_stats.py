import behavior_controller as behavior
import json
import trial_generators as trial
#test_file = '/Users/gunsoo/FieldL/Behavior/data/gk_behav5_20140614_0.trial'
test_file = '/Users/gunsoo/FieldL/Behavior/data/gk_behav5cb14cb10_20140623_0.trial'

controller = behavior.BehaviorController()
controller.params['stimuli_dir'] = '/Users/gunsoo/FieldL/Behavior/stimuli2/';
#controller.stimset_names = ['gk_blk12PitchUp3_Ref1','gk_blk12PitchDown3_Ref1']
controller.stimset_names = ['gk_cb14TempoUp1_Ref1+cb10TempoUp1_Ref1_laser1', 'gk_cb14TempoDown1_Ref1+cb10TempoDown1_Ref1_laser1']
controller.load_stimsets()

fid = open(test_file)
for line in fid.readlines():
	controller.completed_trials.append(json.loads(line))
fid.close()
print controller.calculate_performance_statistics(n_trials_back = 25),'\n'
controller.params['stimset_occurance'] = [0.5, 0.5]

#stims =  trial.generators['gk_without_replacement_adaptive'](controller)
stims =  trial.generators['gk_labeled_laser_without_replacement'](controller)
#print stims,'\n'
for i in range(0,len(stims)):
	print i,':',stims[i]['stimulus']