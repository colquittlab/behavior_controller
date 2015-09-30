## Behavior Operant Controller ##
Jeff Knowles, Doube Lab, 2013 


Behavior Operant Controller (BOC) is a python rolled system to control behavior experiments. It is built to run on a beaglebone black (master branch), but may also be implemented on a host computer communicating with arduinos over usb serial connections (branch gk_stable and arduino).  

## Usage: ##

```
#!bash

python behavior_controller.py config/bird.config 

```

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

## Configuration ##
there is plenty of information on setting up a beaglebone black.  See: http://beagleboard.org/getting-started to connect the first time using usb from your workstation.

deploying boc (should be) easy on a debbian beaglebone using the script bonebootstrap.sh:
```
#!bash

git clone bitbucket.org/spikeCoder/behavior_controller.git
cd behavior controller
sh ./bonebootstrap.sh
```
This covers the basics.  Additional security measures may be advisable on institutional networks.  

Once the bbb is online, I typically ssh in and operate and watch the system using screen.  The deploy script sets up an automatic screen invocation if you like.  
  

## Parts List: ##
* beaglebone black ~$50  [http://beagleboard.org/black]()
* usb soundcard <$10     must be alsa compatible 

###optional:###
* breakout cape