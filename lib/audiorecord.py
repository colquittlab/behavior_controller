#import alsaaudio as aa

import wave
import audioop
from collections import deque
import os
import time
import math
import weakref
import numpy as np

uname = os.uname()[0]
if uname=='Linux': # this allows for development on non-linux systems 
    import alsaaudio as aa
else:
    import pyaudio as pa
     
    #pass

#CHUNK = 256 # CHUNKS of bytes to read each time from mic

#CHANNELS = 1# number of channels
#RATE = 44100# sampling frequency
#THRESHOLD = 5000 # amplitude threshold
#SILENCE_LIMIT = 1 # amount of silence required to stop recording in seconds
#PREV_AUDIO = 0.5 # Previous audio (in seconds) to prepend
#MIN_DUR=1                       #minimum duration in seconds
#INPUT='hw:2,0'
#OUTPUT_DIR='rd58pu12'

class AudioRecord:
    def __init__(self, box, config):
        self.box = weakref.ref(box)
        self.chunk = config.getint('record_params', 'chunk')
        self.format = None
        self.channels = None
        if uname == "Linux":
            self.format = aa.PCM_FORMAT_S16_LE
            self.channels = 1
        else:
            self.format = pa.paInt16
            self.channels = 1

        self.rate = 44100
        self.threshold = config.get('record_params', 'threshold')
        self.silence_limit = config.getfloat('record_params', 'silence_limit')
        self.prev_audio = config.getfloat('record_params', 'prev_audio')
        self.min_dur = config.getfloat('record_params', 'min_dur')
        self.outdir = config.get('record_params', 'outdir')
        self.stream = None

        if self.threshold == "auto":
            self.set_threshold()    

    def audio_int(self, num_samples=64):
        """ Gets max audio intensity for a bunch of chunks of data. Useful for setting threshold.
        """
        print "Getting intensity values from mic."
        values = None
        if uname == "Linux":
        #stream = aa.PCM(aa.PCM_CAPTURE,aa.PCM_NORMAL, INPUT)
            stream = aa.PCM(aa.PCM_CAPTURE,aa.PCM_NORMAL)
            stream.setchannels(self.channels)
            stream.setrate(self.rate)
            stream.setformat(self.format)
            stream.setperiodsize(self.chunk)
            values = [math.sqrt(abs(audioop.max(stream.read()[1], 4)))for x in range(num_samples)]
        else:
            print self.format, self.chunk
            p = pa.PyAudio()
            stream = p.open(rate=self.rate, 
                             format=self.format, 
                             channels=self.channels,
                             frames_per_buffer=self.chunk,
                             input=True)
            values = [math.sqrt(abs(audioop.max(stream.read(self.chunk), 4)))for x in range(num_samples)]

        #values = sorted(values, reverse=True)
        r = sum(values[:int(num_samples * 0.2)]) / int(num_samples * 0.2)
        print "Finished"
        print "max audio intensity is", values
        stream.close()
        return r

    def set_threshold(self):
        values = self.audio_int()
        values_thresh = np.max(values) * 1.5
        print "threshold set to: " + str(values_thresh)
        self.threshold = values_thresh
        return values_thresh 

    def record_song(self):
        # stream = aa.PCM(aa.PCM_CAPTURE,aa.PCM_NORMAL, INPUT)
        if uname == "Linux":
            self.stream = aa.PCM(aa.PCM_CAPTURE,aa.PCM_NORMAL, self.parent.sc_idx)
            self.stream.setchannels(CHANNELS)
            self.stream.setrate(RATE)
            self.stream.setformat(FORMAT)
            self.stream.setperiodsize(CHUNK)
        else:
            p = pa.PyAudio()
            self.stream = p.open(rate=self.rate, 
                             format=self.format, 
                             channels=self.channels,
                             frames_per_buffer=self.chunk,
                             input=True)

        print "listening..."
        audio2send = []
        cur_data = '' # current chunk of audio data
        rel = self.rate/self.chunk
        slid_win = deque(maxlen=self.silence_limit * rel) #amplitude threshold running buffer
        prev_audio = deque(maxlen=self.prev_audio * rel) #prepend audio running buffer
        started = False

        if uname == "Linux":
            cur_data=self.stream.read()[1]
        else:
            cur_data=self.stream.read(self.chunk)
        slid_win.append(math.sqrt(abs(audioop.max(cur_data, 4))))

        while (1):
#            if len(slid_win)>0:
#                print max(slid_win) #uncomment if you want to print intensity values
            if uname == "Linux":
                cur_data=self.stream.read()[1]
            else:
                cur_data=self.stream.read(self.chunk)

            try:
                slid_win.append(math.sqrt(abs(audioop.max(cur_data, 4))))
            except audioop.error:
                print "invalid number of blocks for threshold calculation, but continuing"

            if(sum([x > self.threshold for x in slid_win]) > 0):
                if(not started):
                    # start recording 
                    print "recording"
                    print time.ctime()
                    started = True
                audio2send.append(cur_data)
                print len(audio2send)
            elif (started is True and len(audio2send)>self.min_dur*rel):
                # write out
                print "finished"
                filename = self.save_audio(list(prev_audio) + audio2send)
                started = False
                slid_win = deque(maxlen=self.silence_limit * rel)
                prev_audio = deque(maxlen=self.prev_audio * rel)
                print "listening ..."
                audio2send=[]
            elif (started is True):
                print "duration criterion not met"
                started = False
                slid_win = deque(maxlen=self.silence_limit * rel)
                prev_audio = deque(maxlen=self.prev_audio * rel)
                audio2send=[]
                print "listening ..."
            else:
                prev_audio.append(cur_data)
        print "done recording"
        self.stream.close()

    def save_audio(self, data):
        """ Saves mic data to  WAV file. Returns filename of saved
        file """
        filname = "/".join([str(self.outdir), 'output_'+str(int(time.time()))])
        # writes data to WAV file
        data = ''.join(data)
        wavout = wave.open(filname + '.wav', 'wb')
        wavout.setnchannels(1)
        wavout.setsampwidth(4)
        wavout.setframerate(self.rate) 
        wavout.writeframes(data)
        wavout.close()
        return filname + '.wav'


if(__name__ == '__main__'):
 if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
 audio_int()
 record_song()
