import lib.soundout_tools as so
import time


cardidx = 0
path = "sounds/beep.wav"

so.sendwf(cardidx,path,'.wav',44100,channel=0)
time.sleep(1)
so.sendwf(cardidx,path,'.wav',44100,channel=1)
