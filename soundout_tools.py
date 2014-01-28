import alsaaudio as aa
import wave
from multiprocessing import Process
import numpy as np


# pcm=aa.PCM(aa.PCM_PLAYBACK,aa.PCM_NORMAL,card='hw:1,0')

#functions
def playwf(cardidx, filename, filetype, rate):
	pcm = aa.PCM(type=aa.PCM_PLAYBACK, mode=aa.PCM_NORMAL, card='hw:%d,0'%cardidx)

	if filetype == '.wav':
		song=wave.open(filename)
		"""takes a wave file object and plays it"""
		rate = song.getframerate()
		nchannels=song.getnchannels()
		length=song.getnframes()
		# 8bit is unsigned in wav files
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
		pcm.setchannels(nchannels)
		pcm.setrate(rate)
		pcm.setperiodsize(320)
		data=song.readframes(320)
		while data:
			pcm.write(data)
			data=song.readframes(320)
	elif filetype == '.sng':
		fid= open(filename, 'r')
		nchannels=1
		pcm.setformat(aa.PCM_FORMAT_S32_LE)
		pcm.setchannels(nchannels)
		pcm.setperiodsize(320)
		data = np.fromfile(fid, dtype = np.dtype('d'), count = 320)
		while len(data)>0:
			data = np.array(data*2**15, dtype = np.dtype('i4'))
			pcm.write(data.tostring())
			data = np.fromfile(fid, dtype = np.dtype('d'), count = 320)
		pass
	pcm.close()

def sendwf(pcm, wavefile, filetype, rate):
	p=Process(target = playwf, args = (pcm, wavefile, filetype, rate))
	p.start()

if __name__=="__main__":
	count=0
	while count<100:
		count += 1
		print count
		if count == 1:
			sendwave(pcm, '/home/jknowles/wf_with_spikes.wav')
