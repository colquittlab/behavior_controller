Behavior Operant Controller
Jeff Knowles 2013 


Behavior Operant Controller (BOC) is a python rolled system to control behavior experiments. It is built to run on a beaglebone black (master branch), but may also be implemented on a host computer communicating with arduinos over usb serial connections (branch gk_stable and arduino).  

Usage:
python behavior_controller.py config/bird.config 

config files are stored in config/
Here is an example:

```
#!python
##### example config 
[run_params]
data_dir = /data/behavior/
stimuli_dir = /data/stimuli/
birdname=test
stimset_0=exa1_motif_stimset_a
stimset_1=exa1_motif_stimset_b_2
#stimset_2=exa1_song_a_decomp_probes
mode = discrimination
trial_generator = standard
box = box_1
timeout_light = True
withold_response = False
timeout_period = 30
max_trial_time = 5
feed_time = 5
###
```

## Mode: ##
task specific modes are constructed as python functions that run as loop iterations in a "mainloop". Modes are defined and loaded into a dictionary in the module loop_iterations.py

## Trials: ##
task specific trials are generated using a trial generator.  These are defined in the module trial_generators.py. Trials are produced as trial blocks, which may be useful for statistical regularity.  

 
Parts List: