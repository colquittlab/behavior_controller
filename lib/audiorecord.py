import wave
import audioop
import os
import sys
import time
import math
import weakref
import pdb
import numpy as np
import multiprocessing as mp
from collections import deque

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
    def __init__(self, box):
        #self.box = weakref.ref(box)
        self.box = None
        self.pcm = None
        self.chunk = 1024
        self.format = aa.PCM_FORMAT_S16_LE
        self.channels = 1
        self.rate = 44100
        self.threshold = None
        self.silence_limit = None
        self.prev_audio = None
        self.min_dur = None
        self.outdir = None
        self.recording_queue = None

    def test_config(self):
        self.pcm = 'hw:CARD=Set,DEV=0'
        self.chunk = 256
        self.format = aa.PCM_FORMAT_S16_LE
        self.channels = 1
        self.rate = 44100
        self.silence_limit = 0.5
        self.prev_audio = 0.5
        self.min_dur = 1
        self.outdir = "."

    def init_config(self, config):
        self.chunk = config.getint('record_params', 'chunk')
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

        #if self.threshold == "auto":
        #    self.set_threshold()

    def set_sound_card(self, attr):
        self.pcm = "hw:CARD=%s,DEV=0" % attr

    def audio_int(self, num_samples=64):
        """ Gets max audio intensity for a bunch of chunks of data. Useful for setting threshold.
        """
        print "Getting intensity values from mic."
        values = None
        if uname == "Linux":
        #stream = aa.PCM(aa.PCM_CAPTURE,aa.PCM_NORMAL, INPUT)
            stream = aa.PCM(aa.PCM_CAPTURE,aa.PCM_NORMAL, device=self.pcm)
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

    def start(self):
        self.recording_queue = mp.Queue()
        self.proc = mp.Process(target = start_recording, args= (self.recording_queue,
                                                                self.pcm,
                                                             self.channels,
                                                             self.rate,
                                                             self.format,
                                                             self.chunk,
                                                             self.silence_limit,
                                                             self.prev_audio,
                                                             self.min_dur,
                                                             self.threshold,
                                                             self.outdir))
        self.proc.start()

    def stop(self):
        self.recording_queue.put(1)


def start_recording(queue, pcm, channels, rate, format, chunk,
                    silence_limit, prev_audio_time, min_dur, threshold, outdir):
        # stream = aa.PCM(aa.PCM_CAPTURE,aa.PCM_NORMAL, INPUT)
    stream = None
    if uname == "Linux":
        stream = aa.PCM(aa.PCM_CAPTURE,aa.PCM_NORMAL, device=pcm)
        stream.setchannels(channels)
        stream.setrate(rate)
        stream.setformat(format)
        stream.setperiodsize(chunk)
    else:
        pass
        # p = pa.PyAudio()
        # stream = p.open(rate=self.rate,
        #                  format=self.format,
        #                  channels=self.channels,
        #                  frames_per_buffer=self.chunk,
        #                  input=True)

    print "listening..."
    audio2send = []
    cur_data = '' # current chunk of audio data
    rel = rate/chunk
    slid_win = deque(maxlen=silence_limit * rel) #amplitude threshold running buffer
    prev_audio = deque(maxlen=prev_audio_time * rel) #prepend audio running buffer
    started = False

    if uname == "Linux":
        cur_data=stream.read()[1]
    else:
        pass
        #cur_data=self.stream.read(self.chunk)
    slid_win.append(math.sqrt(abs(audioop.max(cur_data, 4))))

    while queue.empty():
#            if len(slid_win)>0:
#                print max(slid_win) #uncomment if you want to print intensity values
        if uname == "Linux":
            cur_data=stream.read()[1]
        else:
            pass
            #cur_data=self.stream.read(self.chunk)

        try:
            slid_win.append(math.sqrt(abs(audioop.max(cur_data, 4))))
        except audioop.error:
            print "invalid number of blocks for threshold calculation, but continuing"

        if(sum([x > threshold for x in slid_win]) > 0):
            if(not started):
                # start recording
                sys.stdout.write(time.ctime() + ": ")
                sys.stdout.write("recording ... ")
                sys.stdout.flush()
                started = True
            audio2send.append(cur_data)
        elif (started is True and len(audio2send)>min_dur*rel):
            # write out
            print "writing to file"
            filename = save_audio(list(prev_audio) + audio2send, outdir, rate)
            started = False
            slid_win = deque(maxlen=silence_limit * rel)
            prev_audio = deque(maxlen=prev_audio_time * rel)
            print "listening ..."
            audio2send=[]
        elif (started is True):
            print "duration criterion not met"
            started = False
            slid_win = deque(maxlen=silence_limit * rel)
            prev_audio = deque(maxlen=prev_audio_time * rel)
            audio2send=[]
            print "listening ..."
        else:
            prev_audio.append(cur_data)
    else:
        #print "done recording"
        stream.close()
        return

def save_audio(data, outdir, rate):
    """ Saves mic data to  WAV file. Returns filename of saved
    file """
    filname = "/".join([str(outdir), 'output_'+str(int(time.time()))])
    # writes data to WAV file
    data = ''.join(data)
    wavout = wave.open(filname + '.wav', 'wb')
    wavout.setnchannels(1)
    wavout.setsampwidth(4)
    wavout.setframerate(rate)
    wavout.writeframes(data)
    wavout.close()
    return filname + '.wav'

if(__name__ == '__main__'):
 #if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
 audio_int()
 record_song()
