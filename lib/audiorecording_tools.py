#! /usr/bin/env python

import wave
import wavio
import audioop
import os
import sys
import time
import math
import pdb
import datetime
import ConfigParser
import numpy as np
import multiprocessing as mp
import re
# sys.path.append(os.path.expanduser("~") + "/src/behavior_controller")
# import soundout_tools as so
import alsaaudio as aa
import jack
from collections import deque

import soundout_tools as so

uname = os.uname()[0]
# if uname=='Linux': # this allows for development on non-linux systems
#     import alsaaudio as aa
# else:
#     import pyaudio as pa

# from https://scimusing.wordpress.com/2013/10/25/ring-buffers-in-pythonnumpy/
class Ringbuffer():
    "A 1D ring buffer using numpy arrays"
    def __init__(self, length):
        self.data = np.zeros(length, dtype='f')
        self.index = 0

    def __len__(self):
        return self.data.size


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
        self.audio_server = 'alsa'
        self.pcm = None
        self.channel = "1"
        self.pcm_out = None
        self.event_queue = mp.Queue()
        self.control_queue = mp.Queue()
        self.recording_queue = None
        self.running = False
        self.params = {}
        self.proc = None
        self.params['birdname'] = None
        self.params['chunk'] = 1024
        self.params['format'] = aa.PCM_FORMAT_S16_LE
        self.params['channels'] = 1
        self.params['rate'] = 44100
        self.params['threshold'] = None
        self.params['silence_limit'] = 1
        self.params['prev_audio'] = 1
        self.params['min_dur'] = None
        self.params['max_dur'] = None
        self.params['outdir'] = None

    def test_config(self):
        self.set_sound_card(0)
        self.params['birdname']= "test"
        self.params['chunk'] = 1024
        self.params['format'] = aa.PCM_FORMAT_S16_LE
        self.params['channels'] = 1
        self.params['rate'] = 44100
        self.params['silence_limit'] = 0.5
        self.params['prev_audio'] = 1
        self.params['min_dur'] = 1
        self.params['max_dur'] = 10
        self.params['outdir'] = "."

    def init_config(self, config_file):
#        pdb.set_trace()
        if config_file is None:
            self.test_config()
            return
        config = ConfigParser.ConfigParser() 
        config.read(config_file)
        #pdb.set_trace()
        for option in config.options('record_params'):
            if option == "audio_server":
                attr = config.get('record_params', option)
                if not attr in ['jack', 'alsa']:
                    raise(Exception('Error: %s is not a supported audio server' % attr))
                self.audio_server = attr
            elif option == "sound_card":
                attr = config.get('record_params', option)
                self.set_sound_card(attr)
            elif option in ["record_audio"]:
                attr = config.getboolean('record_params',option)
                self.params['record_audio'] = attr
            elif option in ["outdir", "birdname"]:
                attr = config.get('record_params', option)
                self.params[option] = attr
            elif option in ["chunk","channels", 'channel']:
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

#        self.params['outdir'] = "/".join([self.params['outdir'], self.params['bird']])
        if not os.path.exists(self.params['outdir']):
            os.makedirs(self.params['outdir'])

    def set_sound_card(self, attr):
        if isinstance(attr, basestring):
            attr = attr.strip("\"")
        # self.pcm = "hw:CARD=%s,DEV=0" % attr
        #self.pcm = "plughw:%s,0" % attr
        self.pcm = "hw:%s,0" % attr
        # self.pcm = int(attr)

    def set_channel(self, idx):
        self.channel = str(idx)
        
    def set_sound_card_out(self, attr):
        if isinstance(attr, basestring):
            attr = attr.strip("\"")
        # self.pcm = "hw:CARD=%s,DEV=0" % attr
        self.pcm_out = "plughw:%s,0" % attr
        #self.pcm = "hw:%s,0" % attr
        # self.pcm = int(attr)
    def list_sound_cards(self):
        return so.list_sound_cards()

    def audio_int(self, num_samples=64):
        """ Gets max audio intensity for a bunch of chunks of data. Useful for setting threshold.
        """
        print "Getting intensity values from mic."
        values = None
        if uname == "Linux":
        #stream = aa.PCM(aa.PCM_CAPTURE,aa.PCM_NORMAL, INPUT)
            stream = aa.PCM(aa.PCM_CAPTURE,aa.PCM_NORMAL, card=self.pcm)
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

        #values = sorted(values, reverse=True)
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
        if self.audio_server == "jack":
            #pdb.set_trace()
            jack_running = self.check_if_jack_subclient_running()
            if (not jack_running):
                print "Please start jack servers first. Exiting..."
                sys.exit()

        if self.audio_server == 'alsa':
            self.proc = mp.Process(target = start_recording_alsa, args= (self.event_queue,
                                                                self.control_queue,
                                                                self.pcm,
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

        elif self.audio_server == 'jack':
            self.proc = mp.Process(target = start_recording_jack, args= (self.event_queue,
                                                                self.control_queue,
                                                                self.pcm,
                                                                self.params['birdname'],
                                                                self.params['channel'],
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

        print_process = mp.Process(target = print_event_queue, args = (self.event_queue,))
        print_process.start()
        


    def start_return_data(self):
        self.event_queue = mp.Queue()
        self.recording_queue = mp.Queue()
        error_queue = mp.Queue()

        self.proc = mp.Process(target = start_recording_return_data, args= (self.event_queue,
                                                                self.recording_queue,
                                                                            error_queue,
                                                                            #self.audio_server,
                                                                self.pcm,
                                                                self.params['channels'],
                                                                self.params['rate'],
                                                                self.params['format'],
                                                                self.params['chunk']))


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
        if self.audio_server == 'jack':
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


def start_recording_alsa(event_queue, control_queue, pcm, birdname, channels, rate, format, chunk,
                    silence_limit, prev_audio_time, min_dur, max_dur, threshold, outdir):
    stream = None
    print birdname
    if uname == "Linux":
        stream = aa.PCM(aa.PCM_CAPTURE,aa.PCM_NORMAL, card=pcm)
        print format
        print stream.setchannels(int(channels))
        print stream.setformat(format)
        print stream.setperiodsize(chunk)
        print stream.dumpinfo()
    else:
        pass
        # p = pa.PyAudio()
        # stream = p.open(rate=self.params['rate'],
        #                  format=self.params['format'],
        #                  channels=self.params['channels'],
        #                  frames_per_buffer=self.params['chunk'],
        #                  input=True)

    print "AudioRecorder started (listening...)"
    audio2send = []
    cur_data = '' # current chunk of audio data
    rel = rate/chunk
    slid_win = deque(maxlen=silence_limit * rel) #amplitude threshold running buffer
    prev_audio = deque(maxlen=prev_audio_time * rel) #prepend audio running buffer
    started = False
    control_force_record = False
    control_force_record_just_stopped = False

    if uname == "Linux":
        cur_data=stream.read()[1]
    else:
        pass
        #cur_data=self.stream.read(self.params['chunk'])
    slid_win.append(math.sqrt(abs(audioop.max(cur_data, 4))))

    while True:
        ## check whether any events are in queue and if so change control_force_record accordingly
        command = None
        control_force_record_just_stopped = False
        if not control_queue.empty():
            command = control_queue.get(block=True)
            if control_force_record:
                if command == "start":
                    pass
                elif command == "stop":
                    control_force_record = False
                    control_force_record_just_stopped = True
                pass
            else:
                if command == "start":
                    control_force_record = True
                elif command == "stop":
                    pass
                pass

        #if len(slid_win)>0:
        #    print max(slid_win) #uncomment if you want to print intensity values
        if uname == "Linux":
            cur_data=stream.read()[1]
        else:
            pass
            #cur_data=self.stream.read(self.params['chunk'])

        try:
            slid_win.append(math.sqrt(abs(audioop.max(cur_data, 4))))
        except audioop.error:
            print "invalid number of blocks for threshold calculation, but continuing"

        if(sum([x > threshold for x in slid_win]) > 0) or control_force_record:
            if(not started):
                event_queue.put((time.time(), "Audio Recording Started"))
                prev_audio_time_emperical = float(len(prev_audio)) / rel
                recording_start_time = time.time() - prev_audio_time_emperical
                sys.stdout.flush()
                started = True
            audio2send.append(cur_data)

        elif (started is True and len(audio2send)/rel>min_dur and len(audio2send)/rel<max_dur) or control_force_record_just_stopped:
            today = datetime.date.today().isoformat()
            outdir_date = "/".join([outdir, today])
            if not os.path.exists(outdir_date): os.makedirs(outdir_date)
            filename = save_audio_alsa(list(prev_audio) + audio2send, recording_start_time, outdir_date, rate, birdname=birdname, channels=channels)
            event_queue.put((time.time(), "Audio File Saved: %s" % filename))
            started = False
            slid_win = deque(maxlen=silence_limit * rel)
            prev_audio = deque(maxlen=prev_audio_time * rel)
            event_queue.put((time.time(), "Listening"))
            audio2send=[]

        elif (started is True):
            event_queue.put((time.time(), "Duration Criteria not met, listening"))
            started = False
            slid_win = deque(maxlen=silence_limit * rel)
            prev_audio = deque(maxlen=prev_audio_time * rel)
            audio2send=[]

        else:
            prev_audio.append(cur_data)
    else:
        #print "done recording"
        stream.close()
        return

def start_recording_jack(event_queue, control_queue, pcm, birdname, channel, rate, format, chunk,
                    silence_limit, prev_audio_time, min_dur, max_dur, threshold, outdir):
    stream = None
    print birdname
    if uname == "Linux":
        channel = str(channel)
        establish_connection(pcm, channel)
        chunk = jack.get_buffer_size()
        print "Buffer Size:", chunk, "Sample Rate:", rate
        cur_data = np.zeros((1,chunk), 'f')
        dummy = np.zeros((1,0), 'f')
    else:
        pass

    print "AudioRecorder started (listening...)"
    audio2send = []
    rel = rate/chunk
    slid_win = deque(maxlen=silence_limit * rel) #amplitude threshold running buffer
    slid_win_short = Ringbuffer(0.5 * rate) #freq calc running buffer
    prev_audio = Ringbuffer(prev_audio_time * rate) #prepend audio running buffer

    started = False
    control_force_record = True
    control_force_record_just_stopped = False

    if uname == "Linux":

        try:

            jack.process(dummy, cur_data)
        except jack.InputSyncError:
            pass
    else:
        pass
    
    
    slid_win.append(get_audio_power_jack(cur_data[0,:]))
    slid_win_short.extend(cur_data[0,:])
    while True:
        ## check whether any events are in queue and if so change control_force_record accordingly
        command = None
        control_force_record_just_stopped = False
        if not control_queue.empty():
            command = control_queue.get(block=True)
            if control_force_record:
                if command == "start":
                    pass
                elif command == "stop":
                    control_force_record = False
                    #control_force_record_just_stopped = True
                    control_force_record_just_stopped = False #temporary fix
                pass
            else:
                if command == "start":
                    control_force_record = True
                elif command == "stop":
                    pass
                pass

        #if len(slid_win)>0:
        #    print max(slid_win) #uncomment if you want to print intensity values
        if uname == "Linux":
            try:
                jack.process(dummy, cur_data)
            except jack.InputSyncError:
                pass
        else:
            pass
            
        try:
            slid_win.append(get_audio_power_jack(cur_data[0,:]))
            slid_win_short.extend(cur_data[0,:])
        except audioop.error:
            print "invalid number of blocks for threshold calculation, but continuing"

        if(sum([x > threshold for x in slid_win]) > 0) and control_force_record:
           
            if(not started):
                #event_queue.put((time.time(), "Audio Recording Started", slid_win_short.get()))
                event_queue.put((time.time(), "Audio Recording Started"))
                prev_audio_time_emperical = float(len(prev_audio)) / rate
                recording_start_time = time.time() - prev_audio_time_emperical
                sys.stdout.flush()
                started = True
                audio2send = np.array(cur_data[0,:])

            else:
                audio2send = np.append(audio2send, cur_data[0,:])
                #event_queue.put((time.time(), 'audio_threshold_crossing', slid_win_short.get()))
                #event_queue.put((time.time(), 'audio_threshold_crossing'))
            #audio2send.append(cur_data)
            

        elif (started is True and np.shape(audio2send)[0]>min_dur*rate and np.shape(audio2send)[0]<max_dur*rate or control_force_record_just_stopped):
            today = datetime.date.today().isoformat()
            outdir_date = "/".join([outdir, today])
            if not os.path.exists(outdir_date): os.makedirs(outdir_date)
            filename = save_audio_jack(np.append(prev_audio.get(), audio2send), recording_start_time, outdir_date, rate)
            event_queue.put((time.time(), "Audio File Saved: %s" % filename))
            event_queue.put((time.time(), "stop_triggered_audio"))
            event_queue.put((time.time(), "audio_saved"))
            started = False
            slid_win = deque(maxlen=silence_limit * rel)
            #prev_audio = deque(maxlen=prev_audio_time * rel)
            prev_audio = Ringbuffer(prev_audio_time * rate) #prepend audio running buffer
            prev_audio.extend(audio2send)

            event_queue.put((time.time(), "Listening"))
            audio2send = np.array(cur_data[0,:])

        elif (started is True):
            event_queue.put((time.time(), "stop_triggered_audio"))
            event_queue.put((time.time(), "Duration Criteria not met, listening"))
            started = False
            slid_win = deque(maxlen=silence_limit * rel)
            #prev_audio = deque(maxlen=prev_audio_time * rel)
            prev_audio = Ringbuffer(prev_audio_time * rate) #prepend audio running buffer
            prev_audio.extend(audio2send)
            audio2send = np.array(cur_data[0,:])
            #audio2send=[]

        else:
            prev_audio.extend(cur_data[0,:])
            #prev_audio.append(cur_data)
    else:
        #print "done recording"
        jack.deactivate()
        jack.detach()
        return

def start_recording_return_data(event_queue, recording_queue, error_queue, pcm, channels, rate, format, chunk):
    #start_recording_alsa(event_queue, control_queue, pcm, birdname, channels, rate, format, chunk,
    #                silence_limit, prev_audio_time, min_dur, max_dur, threshold, outdir):
    stream = None
    if uname == "Linux":
        # try:

        stream = aa.PCM(aa.PCM_CAPTURE,aa.PCM_NORMAL, card=pcm)
        stream.setchannels(channels)
        stream.setrate(rate)
        stream.setformat(format)
        stream.setperiodsize(chunk)
        # except:
        #     print "here2"
        #     error_queue.put(1)
        #     return
        #     #error_queue.put(1)
        #     #raise aa.ALSAAudioError
        #     #raise
        #     #print "recording2"
        #     #return
    else:
        pass
        # p = pa.PyAudio()
        # stream = p.open(rate=self.params['rate'],
        #                  format=self.params['format'],
        #                  channels=self.params['channels'],
        #                  frames_per_buffer=self.params['chunk'],
        #                  input=True)

    print "listening..."
    audio2send = []
    cur_data = '' # current chunk of audio data
    rel = rate/chunk
    started = False

    if uname == "Linux":
        cur_data=stream.read()[1]
        recording_queue.put(cur_data)
    else:
        pass
        #cur_data=self.stream.read(self.params['chunk'])

    while event_queue.empty():
#            if len(slid_win)>0:
#                print max(slid_win) #uncomment if you want to print intensity values
        if uname == "Linux":
            #if self.audio_server == 'jack':
            #    try:
            #        jack.process(dummy, cur_data)
            #        tmp = get_audio_power(cur_data[0,:])
            #        recording_queue.put(tmp)
            #    except jack.InputSyncError:
            #        print "InputSyncError"
            #else:
            cur_data=stream.read()[1]
            recording_queue.put(cur_data)
        else:
            pass
            #cur_data=self.stream.read(self.params['chunk'])
    else:
        #if self.audio_server == 'jack':
        #    jack.deactivate()
        #    jack.detach()
        #else:
        stream.close()
        return

def save_audio_alsa(data, recording_start_time, outdir, rate, birdname = '', channels=1):
    """ Saves mic data to  WAV file. Returns filename of saved file """
    # filname = "/".join([str(outdir), 'output_'+str(int(time.time()))])
    filname = "/".join([str(outdir), 'output_'+ str(recording_start_time).replace(".","p")])
    filname = filname.replace("//","/")
    #print filname
    # writes data to WAV file
    data = ''.join(data)
    wavout = wave.open(filname + '.wav', 'wb')
    wavout.setnchannels(channels)
    wavout.setsampwidth(2)
    wavout.setframerate(rate)
    wavout.writeframes(data)
    wavout.close()
    return filname + '.wav'

def save_audio_jack(data, recording_start_time, outdir, rate):
    """ Saves mic data recorded using jack server to  WAV file. Returns filename of saved file """
    #filename = "/".join([str(outdir), 'output_'+str(int(time.time()))]) + ".wav"
    filename = "/".join([str(outdir), 'output_'+ str(recording_start_time).replace(".","p")])
    filename = filename.replace("//","/")
    scale_factor = (-.1, .1) # this is hand set for a 24-bit presonus amp. will need to make dynamic later
    wavio.write(filename + '.wav', data, rate, sampwidth=3, scale=scale_factor)
    return filename + '.wav'

def get_audio_power(data):
    return math.sqrt(abs(audioop.max(data, 4)))

def get_audio_power_jack(data):
    tmp = np.array((2**15-1)*data.transpose(),dtype="float",order="C").transpose()
    return np.max(np.abs(tmp))

def print_event_queue(event_queue):
    while True:
        print event_queue.get(block=True)


if(__name__ == '__main__'):
    recorder = AudioRecord()
    if len(sys.argv) > 1:
        recorder.init_config(sys.argv[1])
    else:
        recorder.default_config()
    
    recorder.start()

    print_process = mp.Process(target = print_event_queue, args = (recorder.event_queue,))
    print_process.start()
