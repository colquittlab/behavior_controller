#! /usr/bin/env python

import os
import sys
import re
import time
import math
import pdb
import datetime
import ConfigParser
import wave
import wavio
import audioop
import numpy as np
import multiprocessing as mp
from collections import deque
from subprocess import Popen

sys.path.append(os.path.expanduser("~") + "/src/behavior_controller")
import lib.soundout_tools as so

uname = os.uname()[0]
if uname=='Linux': # this allows for development on non-linux systems
    import alsaaudio as aa
    import jack
else:
    import pyaudio as pa

# from https://scimusing.wordpress.com/2013/10/25/ring-buffers-in-pythonnumpy/
class Ringbuffer():
    "A 1D ring buffer using numpy arrays"
    def __init__(self, length):
        self.data = np.zeros(length, dtype='f')
        self.index = 0

    def extend(self, x):
        "adds array x to ring buffer"
        x_index = (self.index + np.arange(x.size)) % self.data.size
        self.data[x_index] = x
        self.index = x_index[-1] + 1

    def get(self):
        "Returns the first-in-first-out data in the ring buffer"
        idx = (self.index + np.arange(self.data.size)) %self.data.size
        return self.data[idx]

class AudioRecord:
    def __init__(self):
        self.pcm = None
        self.channel = "1"
        self.event_queue = None
        self.recording_queue = None
        self.running = False
        self.params = {}
        self.params['birdname'] = None
        self.params['chunk'] = 1024
        self.params['format'] = aa.PCM_FORMAT_S16_LE
        self.params['channels'] = 2
        self.params['rate'] = 44100
        self.params['threshold'] = None
        self.params['silence_limit'] = None
        self.params['prev_audio'] = None
        self.params['min_dur'] = None
        self.params['max_dur'] = None
        self.params['outdir'] = None

    def test_config(self):
        self.pcm = 'hw:CARD=usbaudio_2,DEV=0'

        self.params['chunk'] = 256
        self.params['format'] = aa.PCM_FORMAT_S16_LE
        self.params['channels'] = 1
        self.params['rate'] = 44100
        self.params['silence_limit'] = 0.5
        self.params['prev_audio'] = 1
        self.params['min_dur'] = 1
        self.params['max_dur'] = 1
        self.params['outdir'] = "."

    def init_config(self, config_file):
        if config_file is None:
            self.test_config()
            return
        config = ConfigParser.ConfigParser()
        config.read(config_file)
        for option in config.options('record_params'):
            if option == "sound_card":
                attr = config.get('record_params', option)
                self.set_sound_card(attr)
            elif option in ["data_dir", "birdname"]:
                attr = config.get('record_params', option)
                self.params[option] = attr
            elif option in ["chunk", "channel", "channels"]:
                attr = config.getint('record_params', option)
                self.params[option] = attr
            else:
                attr = config.getfloat('record_params', option)
                self.params[option] = attr
        if config.has_section('run_params'):
            for option in config.options('run_params'):
                if option in ["data_dir", "birdname"]:
                    attr = config.get("run_params", option)
                    self.params[option] = attr

        self.params['outdir'] = "/".join([self.params['data_dir'], self.params['birdname']])
        if not os.path.exists(self.params['outdir']):
            os.makedirs(self.params['outdir'])

    def set_sound_card(self, attr):
        if isinstance(attr, basestring):
            attr = attr.strip("\"")
        self.pcm = "hw:%s,0" % attr

    def set_channel(self, idx):
        self.channel = str(idx)

    def list_sound_cards(self):
        return so.list_sound_cards()

    ### NOT WORKING WITH CURRENT SETUP ###
    def audio_int(self, num_samples=64):
        """ Gets max audio intensity for a bunch of chunks of data. Useful for setting threshold.
        """
        print "Getting intensity values from mic."
        values = None
        if uname == "Linux":
        #stream = aa.PCM(aa.PCM_CAPTURE,aa.PCM_NORMAL, INPUT)
            stream = aa.PCM(aa.PCM_CAPTURE,aa.PCM_NORMAL, device=self.pcm)
            stream.setchannels(self.params['channels'])
            stream.setrate(self.params['rate'])
            stream.setformat(self.params['format'])
            stream.setperiodsize(self.params['chunk'])
            values = [math.sqrt(abs(audioop.max(stream.read()[1], 4)))for x in range(num_samples)]
        else:
            print self.params['format'], self.params['chunk']
            p = pa.PyAudio()
            stream = p.open(rate=self.params['rate'],
                             format=self.params['format'],
                             channels=self.params['channels'],
                             frames_per_buffer=self.params['chunk'],
                             input=True)
            values = [math.sqrt(abs(audioop.max(stream.read(self.params['chunk']), 4)))for x in range(num_samples)]

        r = sum(values[:int(num_samples * 0.2)]) / int(num_samples * 0.2)
        print "Finished"
        print "max audio intensity is", values
        stream.close()
        return r

    def set_threshold(self):
        values = self.audio_int()
        values_thresh = np.max(values) * 1.1
        print "threshold set to: " + str(values_thresh)
        self.threshold = values_thresh
        return values_thresh

    def attach_to_jack(self):
        jack.attach("mainserver")

    def check_if_jack_subclient_running(self):
        self.attach_to_jack() # this is probably not the best spot for this...
        myname = jack.get_client_name()
        ports = jack.get_ports()
        res = [re.search(self.pcm, p) for p in ports]
        return any(res)

    def start_jack_subclient(self):
        print "Starting jack subclient..."
        cmd = ['alsa_in',
           '-j', self.pcm,
           '-d', self.pcm,
               '-c', str(self.params['channels']),
               '-r', str(self.params['rate']),
               '-q', str(1)]
        self.jack_client_process = Popen(cmd)
        time.sleep(2)

    def start(self):
        self.running = True
        self.event_queue = mp.Queue()
        jack_running = self.check_if_jack_subclient_running()
        if (not jack_running):
            print "Please start jack servers first. Exiting..."
            sys.exit()

        self.proc = mp.Process(target = start_recording, args= (self.event_queue,
                                                                self.pcm,
                                                                self.params['channel'],
                                                                self.params['birdname'],
                                                                self.params['channels'],
                                                                self.params['rate'],
                                                                self.params['format'],
                                                                self.params['chunk'],
                                                                self.params['silence_limit'],
                                                                self.params['prev_audio'],
                                                                self.params['min_dur'],
                                                                self.params['max_dur'],
                                                                self.params['threshold'],
                                                                self.params['outdir']))
        self.proc.start()

    def start_return_data(self):
        self.event_queue = mp.Queue()
        self.recording_queue = mp.Queue()
        error_queue = mp.Queue()
        print "Current channel", self.channel
        jack_running = self.check_if_jack_subclient_running()
        if (not jack_running):
            print "Please start jack servers first. Exiting..."
            sys.exit()

        self.proc = mp.Process(target = start_recording_return_data, args= (self.event_queue,
                                                                            self.recording_queue,
                                                                            error_queue,
                                                                            self.pcm,
                                                                            self.channel,
                                                                            self.params['channels'],
                                                                            self.params['rate'],
                                                                            self.params['format'],
                                                                            self.params['chunk']))

        print "Starting recording..."
        self.proc.start()

        ### Check if mic connection good ###
        current_time = time.time()
        max_time = 1
        while (time.time() - current_time) < max_time:
            if not error_queue.empty():
                raise Exception

    def stop(self):
        self.running = False
        self.event_queue.put(1)
        self.jack_client_process.kill()
        jack.deactivate()
        jack.detach()

def establish_connection(pcm, channel):
    myname = jack.get_client_name()
    capture_name = pcm + ":capture_" + channel
    port_name = "in_" + channel
    connection_name = myname+":"+port_name

    print capture_name, port_name, connection_name
    print "Jack ports (before):", jack.get_ports()
    jack.register_port(port_name, jack.IsInput)
    jack.activate()
    print "Jack ports (after):", jack.get_ports()
    jack.connect(capture_name, connection_name)
    print jack.get_connections(connection_name)

def start_recording(queue, pcm, channel, birdname, channels, rate, format, chunk,
                    silence_limit, prev_audio_time, min_dur, max_dur, threshold, outdir):
    stream = None
    if uname == "Linux":
        channel = str(channel)
        establish_connection(pcm, channel)
        chunk = jack.get_buffer_size()
        print "Buffer Size:", chunk, "Sample Rate:", rate
        cur_data = np.zeros((1,chunk), 'f')
        dummy = np.zeros((1,0), 'f')

    else:
        pass

    print "listening..."
    audio2send = None
    rel = rate/chunk
    slid_win = deque(maxlen=silence_limit * rel) #amplitude threshold running buffer
    prev_audio = Ringbuffer(prev_audio_time * rate) #prepend audio running buffer
    started = False

    if uname == "Linux":
        try:
            jack.process(dummy, cur_data)
        except jack.InputSyncError:
            pass
    else:
        pass

    while queue.empty():
        if uname == "Linux":
            try: 
                jack.process(dummy, cur_data)
            except jack.InputSyncError:
                pass
        else:
            pass
        try:
            slid_win.append(get_audio_power(cur_data[0,:]))
        except audioop.error:
            print "invalid number of blocks for threshold calculation, but continuing"

        if(sum([x > threshold for x in slid_win]) > 0):
            if(not started):
                # start recording
                sys.stdout.write(birdname + ", ")
                sys.stdout.write(time.ctime() + ": ")
                sys.stdout.write("recording ... ")
                sys.stdout.flush()
                started = True
                audio2send = np.array(cur_data[0,:])
            else:
                audio2send = np.append(audio2send, cur_data[0,:])
        elif (started is True and np.shape(audio2send)[0]>min_dur*rate and np.shape(audio2send)[0]<max_dur*rate):
            # write out
            print "writing to file"
            today = datetime.date.today().isoformat()
            outdir_date = "/".join([outdir, today])
            if not os.path.exists(outdir_date): os.makedirs(outdir_date)
            filename = save_audio(np.append(prev_audio.get(), audio2send), outdir_date, rate)
            started = False
            slid_win = deque(maxlen=silence_limit * rel)
            prev_audio = Ringbuffer(prev_audio_time * rate) #prepend audio running buffer
            prev_audio.extend(audio2send)
            print "listening ..."
            audio2send = None
        elif (started is True):
            print "duration criterion not met"
            started = False
            slid_win = deque(maxlen=silence_limit * rel)
            prev_audio = Ringbuffer(prev_audio_time * rate) #prepend audio running buffer
            prev_audio.extend(audio2send)
            audio2send = None
            print "listening ..."
        else:
            prev_audio.extend(cur_data[0,:])

    else:
        jack.deactivate()
        jack.detach()
        return

def start_recording_return_data(event_queue, recording_queue, error_queue, pcm, channel, channels, rate, format, chunk):
    stream = None
    if uname == "Linux":
        try:
            establish_connection(pcm, channel)
            chunk = jack.get_buffer_size()
            print "Buffer Size:", chunk, "Sample Rate:", rate
            cur_data = np.zeros((1,chunk), 'f')
            dummy = np.zeros((1,0), 'f')
        except:
            print "here2"
            raise
            error_queue.put(1)
            return
    else:
        pass
        # p = pa.PyAudio()
        # stream = p.open(rate=self.params['rate'],
        #                  format=self.params['format'],
        #                  channels=self.params['channels'],
        #                  frames_per_buffer=self.params['chunk'],
        #                  input=True)

    print "listening..."
    if uname == "Linux":
        try:
            jack.process(dummy, cur_data)
            tmp = cur_data[0,:]
            recording_queue.put(tmp)
        except jack.InputSyncError:
            print "InputSyncError"
    else:
        pass
    while event_queue.empty():
        if uname == "Linux":
            try:
                jack.process(dummy, cur_data)
                tmp = get_audio_power(cur_data[0,:])
                recording_queue.put(tmp)
            except jack.InputSyncError:
                print "InputSyncError"
        else:
            pass
            #cur_data=self.stream.read(self.params['chunk'])
    else:
        jack.deactivate()
        jack.detach()
        return

def save_audio(data, outdir, rate):
    """ Saves mic data to  WAV file. Returns filename of saved file """
    filename = "/".join([str(outdir), 'output_'+str(int(time.time()))]) + ".wav"
    scale_factor = (-.1, .1) # this is hand set for a 24-bit presonus amp. will need to make dynamic later
    wavio.write(filename, data, rate, sampwidth=3, scale=scale_factor)
    return filename + '.wav'

def get_audio_power(data):
    tmp = np.array((2**15-1)*data.transpose(),dtype="float",order="C").transpose()
    return np.max(np.abs(tmp))

def main(argv):
    recorder = AudioRecord()
    if len(argv) > 1:
        recorder.init_config(argv[1])
    else:
        recorder.test_config()
    recorder.start()

if(__name__ == '__main__'):
    main(sys.argv)
