#! /usr/bin/env python

import wave
import audioop
import os
import sys
import time
import math
import pdb
import datetime
import ConfigParser
import numpy as np
import scipy.io.wavfile
import multiprocessing as mp

sys.path.append(os.path.expanduser("~") + "/src/behavior_controller")
import lib.soundout_tools as so
from collections import deque
from subprocess import Popen

uname = os.uname()[0]
if uname=='Linux': # this allows for development on non-linux systems
    import alsaaudio as aa
    import jack
else:
    import pyaudio as pa

class AudioRecord:
    def __init__(self):
        self.pcm = None
        self.event_queue = None
        self.recording_queue = None
        self.running = False
        self.params = {}
        self.params['birdname'] = None
        self.params['chunk'] = 1024
        self.params['format'] = aa.PCM_FORMAT_S16_LE
        self.params['channels'] = 1
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
#        pdb.set_trace()
        if config_file is None:
            self.test_config()
            return
        config = ConfigParser.ConfigParser() 
        config.read(config_file)
        #pdb.set_trace()
        for option in config.options('record_params'):
            if option == "sound_card":
                attr = config.get('record_params', option)
                self.set_sound_card(attr)
            elif option in ["data_dir", "birdname"]:
                attr = config.get('record_params', option)
                self.params[option] = attr
            elif option == "chunk":
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
        #self.pcm = "hw:CARD=%s,DEV=0" % attr
        self.pcm = "hw:%s,0" % attr

    def list_sound_cards(self):
        return so.list_sound_cards()

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

    def start_jack_subclient(self, pcm, channels, rate):
#        pcms = [p for p in pcms if re.search("^hw", p)]
#        device = [p for p in pcms if re.search(self.sound_card, p)]
        print "Starting jack subclient..."
        cmd = ['alsa_in', 
           '-j', pcm,
           '-d', pcm,
           '-c', str(channels),
               '-r', str(rate),
               '-q', str(1)]
        self.jack_client_process = Popen(cmd)
        time.sleep(2)
        #print self.jack_client_process


    def start(self):
        self.running = True
        self.event_queue = mp.Queue()
        self.start_jack_subclient(self.pcm, self.params['channels'], self.params['rate'])
        self.proc = mp.Process(target = start_recording, args= (self.event_queue,
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
        self.proc.start()

    def start_return_data(self):
        self.event_queue = mp.Queue()
        self.recording_queue = mp.Queue()
        error_queue = mp.Queue()
        self.start_jack_subclient(self.pcm, self.params['channels'], self.params['rate'])
        
        print "here"
        print  self.pcm, self.params['channels'], self.params['rate']
        #self.jack_proc = mp.Process(target = start_jack_subclient, args = (
        #                                                                   self.pcm, 
        #                                                                   self.params['channels'], 
        #                                                                   self.params['rate']))
        print "here"
        #self.jack_proc.start()
        self.proc = mp.Process(target = start_recording_return_data, args= (self.event_queue,
                                                                            self.recording_queue,
                                                                            error_queue,
                                                                self.pcm,
                                                                            #self.params['sound_card'],
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
    
def start_jack_subclient(pcm, channels, rate):
    print "Starting jack subclient..."
    cmd = ['alsa_in', 
           '-j', pcm,
           '-d', pcm,
           '-c', str(channels),
           '-r', str(rate)]
    jack_client_process = Popen(cmd)

def start_recording(queue, pcm, birdname, channels, rate, format, chunk,
                    silence_limit, prev_audio_time, min_dur, max_dur, threshold, outdir):
    stream = None
    if uname == "Linux":
        jack.attach("mainserver")
        myname = jack.get_client_name()
        print "Client:", myname
        print "Jack ports (before):", jack.get_ports()
        jack.register_port("in_1", jack.IsInput)
        jack.activate()
        print "Jack ports (after):", jack.get_ports()
        jack.connect(pcm + ":capture_1", myname + ":in_1")
        print jack.get_connections(myname+":in_1")
        chunk = jack.get_buffer_size()
        print "Buffer Size:", chunk, "Sample Rate:", rate
        cur_data = np.zeros((1,chunk), 'f')
        dummy = np.zeros((1,0), 'f')
       
    else:
        pass
        # p = pa.PyAudio()
        # stream = p.open(rate=self.params['rate'],
        #                  format=self.params['format'],
        #                  channels=self.params['channels'],
        #                  frames_per_buffer=self.params['chunk'],
        #                  input=True)

    print "listening..."
    #audio2send = np.zeros((1,chunk))
    #audio2send = np.zeros(0)
    audio2send = None
    print rate, chunk
    rel = rate/chunk
    slid_win = deque(maxlen=silence_limit * rel) #amplitude threshold running buffer
    prev_audio = deque(maxlen=prev_audio_time * rate) #prepend audio running buffer
    started = False

    if uname == "Linux":
        try:
            jack.process(dummy, cur_data)            
        except jack.InputSyncError:
            pass
    else:
        pass
        #cur_data=self.stream.read(self.params['chunk'])
    #tmp = np.array((2**23-1)*cur_data.transpose(),dtype="float",order="C")
    #slid_win.append(math.sqrt(abs(audioop.max(cur_data, 4))))
    #slid_win.append(math.sqrt(abs(audioop.max(tmp, 4))))
    width = 3
    while queue.empty():
        #if len(slid_win)>0:
        #    print max(slid_win) #uncomment if you want to print intensity values
        if uname == "Linux":
            try: 
                jack.process(dummy, cur_data)            
                #            cur_data=stream.read()[1]
            except jack.InputSyncError:
                pass
        else:
            pass
            #cur_data=self.stream.read(self.params['chunk'])

        try:
            print cur_data
            #tmp = np.array((2**23-1)*cur_data.transpose(),dtype="float",order="C").transpose()
            tmp = np.array((2**(8*width-1)-1)*cur_data.transpose(),dtype="float",order="C").transpose()
            #tmp = math.sqrt(abs(audioop.max(cur_data, 2)))
            #print tmp
            tmp2 = np.max(tmp)
            #print tmp2
            #slid_win.append(math.sqrt(abs(audioop.max(tmp, 4))))
            slid_win.append(tmp2)
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
            print np.shape(audio2send), np.shape(cur_data[0,:])
            audio2send = np.append(audio2send, cur_data[0,:])
            #audio2send = np.append(audio2send, cur_data, axis=0)
            #print np.shape(audio2send)[0], min_dur*rel
            print np.shape(audio2send), min_dur*rate
#        elif (started is True and np.shape(audio2send)[0]>min_dur*rel and np.shape(audio2send)[0]<max_dur*rel):
        elif (started is True and np.shape(audio2send)[0]>min_dur*rate and np.shape(audio2send)[0]<max_dur*rate):
            # write out
            print "writing to file"
            today = datetime.date.today().isoformat()
            outdir_date = "/".join([outdir, today])
            if not os.path.exists(outdir_date): os.makedirs(outdir_date)
            #print outdir_date
#            filename = save_audio(np.append(prev_audio, audio2send), outdir_date, rate)
            filename = save_audio(audio2send, outdir_date, rate)   
            started = False
            slid_win = deque(maxlen=silence_limit * rel)
            prev_audio = deque(maxlen=prev_audio_time * rate)
            print "listening ..."
            audio2send=np.zeros((1,chunk))
        elif (started is True):
            print "duration criterion not met"
            started = False
            slid_win = deque(maxlen=silence_limit * rel)
            prev_audio = deque(maxlen=prev_audio_time * rate)
            audio2send=np.zeros((1,chunk))
            print "listening ..."
        else:
            prev_audio.append(tmp)
            
    else:
        #print "done recording"
        jack.deactivate()
        jack.detach()
#        stream.close()
        return

def start_recording_return_data(event_queue, recording_queue, error_queue, pcm, channels, rate, format, chunk):
    stream = None
    if uname == "Linux":
        try:
            jack.attach("mainserver")
            myname = jack.get_client_name()
            print "Client:", myname
            print "Jack ports (before):", jack.get_ports()

            jack.register_port("in_1", jack.IsInput)

            jack.activate()
            print "Jack ports (after):", jack.get_ports()
            
            jack.connect(pcm + ":capture_1", myname + ":in_1")

            print jack.get_connections(myname+":in_1")

            N = jack.get_buffer_size()
            print "Buffer Size:", N, "Sample Rate:", rate
            cur_data = np.zeros((1,N), 'f')
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
    audio2send = []
    #cur_data = '' # current chunk of audio data
    rel = rate/chunk
    started = False

    if uname == "Linux":
        print N
        try:
            jack.process(dummy, cur_data)            
            tmp = np.array((2**15-1)*cur_data.transpose(),dtype="int16",order="C")

            #tmp = np.sqrt(np.abs(np.max(tmp)))
            print tmp
            #        cur_data=stream.read()[1]
            print np.shape(tmp)
            recording_queue.put(tmp)
        except jack.InputSyncError:
            print "InputSyncError"
    else:
        pass
        #cur_data=self.stream.read(self.params['chunk'])
    width = 3
    while event_queue.empty():
#            if len(slid_win)>0:
#                print max(slid_win) #uncomment if you want to print intensity values
        if uname == "Linux":
            try:
                jack.process(dummy, cur_data)
                #            cur_data=stream.read()[1]
                tmp = np.array((2**(8*width-1)-1)*cur_data.transpose(),dtype="float",order="C")
                #tmp = np.sqrt(np.abs(np.max(tmp)))
                recording_queue.put(tmp)
            except jack.InputSyncError:
                print "InputSyncError"
        else:
            pass
            #cur_data=self.stream.read(self.params['chunk'])
    else:
        jack.deactivate()
        jack.detach()
        #stream.close()
        return

def save_audio(data, outdir, rate):
    """ Saves mic data to  WAV file. Returns filename of saved file """
    filename = "/".join([str(outdir), 'output_'+str(int(time.time()))]) + ".wav"
    print filename
    #data1 = np.array(data[0], dtype="int16", order="C")
    #data1 = data.flatten()
    #xdata1 = ''.join(data1)
#    data2 = np.ndarray((len(data1), 1), buffer=data1)
    print np.shape(data)
#    print np.shape(data1)
 #   print np.shape(data2)
#    print data1
#    scipy.io.wavfile.write(filename, int(rate), data2)
    # writes data to WAV file
    # data = ''.join(data)
    wavout = wave.open(filename, 'wb')
    wavout.setnchannels(1)
    wavout.setsampwidth(4)
    wavout.setframerate(rate)
    wavout.writeframes(data)
    wavout.close()
    return filename + '.wav'

def get_audio_power(data):
    return math.sqrt(abs(audioop.max(data, 4)))

def main(argv):
    recorder = AudioRecord()
    if len(argv) > 1:
        recorder.init_config(argv[1])
    else:
        recorder.test_config()
    recorder.start()

if(__name__ == '__main__'):
    main(sys.argv)

