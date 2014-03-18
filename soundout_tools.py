import os
import wave
from multiprocessing import Process
import numpy as np

if os.uname()[0]=='Linux': # this allows for development on non-linux systems 
	import alsaaudio as aa
else:
	pass


#functions
def playwf(cardidx, filename, filetype, rate):
	# pcm = aa.PCM(type=aa.PCM_PLAYBACK, mode=aa.PCM_NORMAL, card='hw:%d,0'%cardidx)
	pcm = aa.PCM(type=aa.PCM_PLAYBACK, mode=aa.PCM_NORMAL, card='plughw:%d,0'%cardidx)
	frame_size = 320
	if filetype == '.wav':
		song=wave.open(filename)
		"""takes a wave file object and plays it"""
		# rate = song.getframerate()
		nchannels=song.getnchannels()
		length=song.getnframes()
		# 8bit is unsigned in wav files
		pcm.setchannels(nchannels)
		pcm.setrate(rate)
		if song.getsampwidth() == 1:
			pcm.setformat(aa.PCM_FORMAT_U8)
		# Otherwise we assume signed data, little endian
		elif song.getsampwidth() == 2:
			pcm.setformat(aa.PCM_FORMAT_S16_LE)
		elif song.getsampwidth() == 3:
			pcm.setformat(aa.PCM_FORMAT_S24_LE)
		elif song.getsampwidth() == 4:
			pcm.setformat(aa.PCM_FORMAT_S32_LE)
		else:
			raise ValueError('Unsupported format')
		pcm.setperiodsize(frame_size)
		data=song.readframes(frame_size)
		while data:
			pcm.write(data)
			data=song.readframes(frame_size)
	elif filetype == '.sng':
		fid= open(filename, 'r')
		nchannels=1
		pcm.setformat(aa.PCM_FORMAT_S32_LE)
		pcm.setchannels(nchannels)
		pcm.setrate(rate)
		pcm.setperiodsize(frame_size)
		data = np.fromfile(fid, dtype = np.dtype('d'), count = frame_size)
		while len(data) > 0:
			if len(data) < frame_size:
				data = np.append(data, np.zeros((frame_size-len(data), 1)))
			
			data = np.array(data*2**15, dtype = np.dtype('i4'))
			pcm.write(data.tostring())
			data = np.fromfile(fid, dtype = np.dtype('d'), count = frame_size)
	pass
	pcm.close()

def sendwf(pcm, wavefile, filetype, rate):
	p=Process(target = playwf, args = (pcm, wavefile, filetype, rate))
	p.start()

def beep(a=.01, b=500):
	os.system('play --no-show-progress --null --channels 1 synth %s sine %f' % ( a, b))

def list_sound_cards():
	return aa.cards()

if __name__=="__main__":
	# sendwf(1, '/data/doupe_lab/stimuli/boc_syl_discrim_v1_stimset_a/song_a_1.wav','.wav',44100)
	print list_sound_cards()