import alsaaudio as aa
import wave
from multiprocessing import Process


# pcm=aa.PCM(aa.PCM_PLAYBACK,aa.PCM_NORMAL,card='hw:1,0')

#functions
def playwave(cardidx, wavefile):
	pcm = aa.PCM(type=aa.PCM_PLAYBACK, mode=aa.PCM_NORMAL, card='hw:%d,0'%cardidx)
	song=wave.open(wavefile)
	"""takes a wave file object and plays it"""
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
	# pcm.setrate(framerate)
	pcm.setperiodsize(320)
	data=song.readframes(320)
	while data:
		pcm.write(data)
		data=song.readframes(320)
	pcm.close()

def sendwave(pcm,wavefile):
	p=Process(target = playwave, args = (pcm, wavefile))
	p.start()

if __name__=="__main__":
	count=0
	while count<100:
		count += 1
		print count
		if count == 1:
			sendwave(pcm, '/home/jknowles/wf_with_spikes.wav')
