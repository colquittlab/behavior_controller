import os
import wave
from multiprocessing import Process
import numpy as np

if os.uname()[0]=='Linux': # this allows for development on non-linux systems 
	import alsaaudio as aa
else:
	pass


#functions
def playwf(cardidx, filename, filetype, rate, pulse = False, pulse_type = "high"):
	# pcm = aa.PCM(type=aa.PCM_PLAYBACK, mode=aa.PCM_NORMAL, card='hw:%d,0'%cardidx)
	pcm = aa.PCM(type=aa.PCM_PLAYBACK, mode=aa.PCM_NORMAL, card='plughw:%d,0'%cardidx)
	frame_size = 320
	if filetype == '.wav':
		song=wave.open(filename)
		"""takes a wave file object and plays it"""
		# rate = song.getframerate()
		if pulse:
			nchannels=2
			pcm.setperiodsize(frame_size)
		else:
			nchannels=1
			pcm.setperiodsize(frame_size)
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
		data=song.readframes(frame_size)
		while data:
			if pulse:
				# x = np.fromstring(data, np.int16)
				# x = np.expand_dims(x,axis=1)
				# x = np.concatenate((x, 0*np.ones(x.shape)), axis = 1)
				# data = x.flatten().tostring()
				pcm.write(data)
				
				# data = np.concatinate(np.array(data), np.one
			else:
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
	pcm.close()
	pass

def sendwf(pcm, wavefile, filetype, rate, pulse = False, pulse_type = "high"):
	kwargs = {'pulse': pulse, 'pulse_type': pulse_type}
	p=Process(target = playwf, args = (pcm, wavefile, filetype, rate), kwargs = kwargs)
	p.start()
	pass

def beep(a=.01, b=500):
	os.system('play --no-show-progress --null --channels 1 synth %s sine %f' % ( a, b))
	pass

def list_sound_cards():
	return aa.cards()

if __name__=="__main__":
	# song1 = wave.open('/home/jknowles/test.wav')
	# song2 = wave.open('/home/jknowles/test1ch.wav')
	# import ipdb; ipdb.set_trace()

	sendwf(1, '/home/jknowles/data/doupe_lab/stimuli/boc_syl_discrim_v1_stimset_a/song_a_1.wav','.wav',44100, pulse = False)
	# playwf(1, '/home/jknowles/test.wav','.wav',44100, pulse = True)
	# playwf(1, '/home/jknowles/test1ch.wav','.wav',44100, pulse = True)
	
	print list_sound_cards()
