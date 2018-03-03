import os
import wave
from multiprocessing import Process, Value
import subprocess
import numpy as np
import pdb
if os.uname()[0]=='Linux': # this allows for development on non-linux systems
        import alsaaudio as aa
else:
        pass


#functions
def play_alsa(stopsig, cardidx, filename, filetype, rate, pulse, pulse_type):
    frame_size = 320
    pcm = aa.PCM(type=aa.PCM_PLAYBACK, mode=aa.PCM_NORMAL, card='plughw:%d,0'%cardidx)
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
        while data and stopsig.value==0:
            if pulse:
                    # x = np.fromstring(data, np.int16)
                    # x = np.expand_bebbdims(x,axis=1)
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
        while len(data) > 0 and stopsig.value==0:
            if len(data) < frame_size:
                data = np.append(data, np.zeros((frame_size-len(data), 1)))
            data = np.array(data*2**15, dtype = np.dtype('i4'))
            pcm.write(data.tostring())
            data = np.fromfile(fid, dtype = np.dtype('d'), count = frame_size)
    pcm.close()
    stopsig.value = 1
    pass

def play_pyaudio(stopsig, cardidx, filename, filetype, rate, pulse, pulse_type):
    frame_size = 320
    p = pa.PyAudio()

    if filetype == '.wav':
        song=wave.open(filename)
        """takes a wave file object and plays it"""
        # rate = song.getframerate()
        nchannels = None
        if pulse:
            nchannels=2
            #pcm.setperiodsize(frame_size)
        else:
            nchannels=1
            #pcm.setperiodsize(frame_size)
        length=song.getnframes()
        # 8bit is unsigned in wav files
#	pcm.setchannels(nchannels)
        #pcm.setrate(rate)
        format = p.get_format_from_width(song.getsampwidth())
#	if song.getsampwidth() == 1:
#            format = p)
        # Otherwise we assume signed data, little endian
#	elif song.getsampwidth() == 2:
#		pcm.setformat(aa.PCM_FORMAT_S16_LE)
#	elif song.getsampwidth() == 3:
#		pcm.setformat(aa.PCM_FORMAT_S24_LE)
#	elif song.getsampwidth() == 4:
#		pcm.setformat(aa.PCM_FORMAT_S32_LE)
#	else:
#		raise ValueError('Unsupported format')
        print format
        pcm = p.open(rate=44100,
                         format=4,
                         channels=1,
                         frames_per_buffer=320,
                         output=True)
        data=song.readframes(frame_size)
        while data and stopsig.value==0:
            if pulse:
                # x = np.fromstring(data, np.int16)
                # x = np.expand_bebbdims(x,axis=1)
                # x = np.concatenate((x, 0*np.ones(x.shape)), axis = 1)
                # data = x.flatten().tostring()
                #pcm.write(data)
                pass

                # data = np.concatinate(np.array(data), np.one
            else:
                #pcm.write(data)
                pass
            data=song.readframes(frame_size)

    #elif filetype == '.sng':
    #    fid= open(filename, 'r')
#	nchannels=1
#	pcm.setformat(aa.PCM_FORMAT_S32_LE)
#	pcm.setchannels(nchannels)
#	pcm.setrate(rate)
#	pcm.setperiodsize(frame_size)
#	data = np.fromfile(fid, dtype = np.dtype('d'), count = frame_size)
#	while len(data) > 0 and stopsig.value==0:
#		if len(data) < frame_size:
#			data = np.append(data, np.zeros((frame_size-len(data), 1)))
#		data = np.array(data*2**15, dtype = np.dtype('i4'))
#		pcm.write(data.tostring())
#		data = np.fromfile(fid, dtype = np.dtype('d'), count = frame_size)
#
    pcm.close()
    stopsig.value = 1
    pass

def playwf(stopsig, cardidx, filename, filetype, rate, pulse = False, pulse_type = "high"):
 #   pdb.set_trace()
    #try:
#	mixer.setvolume(100)
#    except:
#	pass
#    try:
#	mixer.setmute(0)
#    except:
#	pass
    print "here"
#    frame_size = 320
#    pcm = None
    if uname == "Linux":
        play_alsa(stopsig, cardidx, filename, filetype, rate, pulse, pulse_type)
    else:
        play_pyaudio(stopsig, cardidx, filename, filetype, rate, pulse, pulse_type)





def sendwf(cardidx, wavefile, filetype, rate, pulse = False, pulse_type = "high"):
        stopsig = Value('i', 0)
        kwargs = {'pulse': pulse, 'pulse_type': pulse_type}
        p=Process(target = playwf, args = (stopsig, cardidx, wavefile, filetype, rate), kwargs = kwargs)
        p.start()
        return (p, stopsig)

def beep(a=.05, b=500):
        command = 'play --no-show-progress --null --channels 1 synth %s sine %f' % ( a, b)
        # print command
        subprocess.Popen([command], stdout=subprocess.PIPE, shell = True)
        #os.popen('play --no-show-progress --null --channels 1 synth %s sine %f' % ( a, b))
        # sendwf(0, '/sounds/beep.wav', '.wav, 44100)
        pass

def list_sound_cards():
        if os.uname()[0]=='Linux':
                return aa.cards()
        else:
                p = pa.PyAudio()
                return [p.get_device_info_by_index(x)['name']
                            for x in range(p.get_device_count())]

if __name__=="__main__":
    import sys
    if len(sys.argv) <= 1:
        raise(Exception('no args passed'))
    else:
        cardidx = int(sys.argv[1])
        spath = sys.argv[2]
    sendwf(cardidx, spath, '.wav',44100,pulse = False)
        # # song1 = wave.open('/home/jknowles/test.wav')
        # # song2 = wave.open('/home/jknowles/test1ch.wav')
        # # import ipdb; ipdb.set_trace()

        # sendwf(1, '/home/jknowles/data/doupe_lab/stimuli/boc_syl_discrim_v1_stimset_a/song_a_1.wav','.wav',44100, pulse = False)
        # # playwf(1, '/home/jknowles/test.wav','.wav',44100, pulse = True)
        # # playwf(1, '/home/jknowles/test1ch.wav','.wav',44100, pulse = True)


