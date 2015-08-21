import alsaaudio as aa
import wave
import audioop
from collections import deque
import os
import time
import math



CHUNK = 256 # CHUNKS of bytes to read each time from mic
FORMAT = aa.PCM_FORMAT_S16_LE #this is the standard wav data format (16bit little endian)
CHANNELS = 1# number of channels
RATE = 44100# sampling frequency
THRESHOLD = 5000 # amplitude threshold
SILENCE_LIMIT = 1 # amount of silence required to stop recording in seconds
PREV_AUDIO = 0.5 # Previous audio (in seconds) to prepend
MIN_DUR=1#minimum duration in seconds
INPUT='hw:2,0'
OUTPUT_DIR='rd58pu12'

def audio_int(num_samples=64):
 """ Gets max audio intensity for a bunch of chunks of data. Useful for setting threshold.
 """
 print "Getting intensity values from mic."
 #stream = aa.PCM(aa.PCM_CAPTURE,aa.PCM_NORMAL, INPUT)
 stream = aa.PCM(aa.PCM_CAPTURE,aa.PCM_NORMAL)
 stream.setchannels(CHANNELS)
 stream.setrate(RATE)
 stream.setformat(FORMAT)
 stream.setperiodsize(CHUNK)
 values = [math.sqrt(abs(audioop.max(stream.read()[1], 4)))for x in range(num_samples)]
 #values = sorted(values, reverse=True)
 r = sum(values[:int(num_samples * 0.2)]) / int(num_samples * 0.2)
 print "Finished"
 print "max audio intensity is", values
 stream.close()
 return r
 
def record_song(threshold=THRESHOLD):
# stream = aa.PCM(aa.PCM_CAPTURE,aa.PCM_NORMAL, INPUT)
 stream = aa.PCM(aa.PCM_CAPTURE,aa.PCM_NORMAL)
 stream.setchannels(CHANNELS)
 stream.setrate(RATE)
 stream.setformat(FORMAT)
 stream.setperiodsize(CHUNK)
 print "Listening"
 audio2send = []
 cur_data = '' # current chunk of audio data
 rel = RATE/CHUNK
 slid_win = deque(maxlen=SILENCE_LIMIT * rel) #amplitude threshold running buffer
 prev_audio = deque(maxlen=PREV_AUDIO * rel) #prepend audio running buffer
 started = False
 curr_data=stream.read()[1]
 slid_win.append(math.sqrt(abs(audioop.max(cur_data, 4)))) 
 while (1):
#  if len(slid_win)>0:
#   print max(slid_win) #uncomment if you want to print intensity values
  cur_data = stream.read()[1]
  try:
   slid_win.append(math.sqrt(abs(audioop.max(cur_data, 4))))
  except audioop.error:
   print "invalid number of blocks for threshold calculation, but continuing"
  if(sum([x > THRESHOLD for x in slid_win]) > 0):
   if(not started):
    print "recording"
    print time.ctime()
    started = True
   audio2send.append(cur_data)
  elif (started is True and len(audio2send)>MIN_DUR*rel):
   print "Finished"
   filename = save_audio(list(prev_audio) + audio2send)
   started = False
   slid_win = deque(maxlen=SILENCE_LIMIT * rel)
   prev_audio = deque(maxlen=0.5 * rel)
   print "Listening ..."
   audio2send=[]
  elif (started is True):
   print "duration criterion not met"
   started = False
   slid_win = deque(maxlen=SILENCE_LIMIT * rel)
   prev_audio = deque(maxlen=0.5 * rel)
   audio2send=[]
   print "Listening ..."
  else:
   prev_audio.append(cur_data)
 print "done recording"
 stream.close()

def save_audio(data):
 """ Saves mic data to  WAV file. Returns filename of saved
 file """
 filname = "/".join([OUTPUT_DIR, 'output_'+str(int(time.time()))])
 # writes data to WAV file
 data = ''.join(data)
 wavout = wave.open(filname + '.wav', 'wb')
 wavout.setnchannels(1)
 wavout.setsampwidth(4)
 wavout.setframerate(RATE) 
 wavout.writeframes(data)
 wavout.close()
 return filname + '.wav'


if(__name__ == '__main__'):
 if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
 audio_int()
 record_song()
