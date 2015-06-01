import alsaaudio as aa



count = 0
cardidx = 0
while True:
	count += 1
	#try:
	pcm = aa.PCM(type=aa.PCM_PLAYBACK, mode=aa.PCM_NORMAL, card='plughw:%d,0'%cardidx)
		#pcm.close()
	#except:
		#import ipdb; ipdb.set_trace()

