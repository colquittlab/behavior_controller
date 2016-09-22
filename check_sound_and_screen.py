import lib.soundout_tools as so
import behavior_controller as bc
import time


cardidx = 0
path = "sounds/beep.wav"




# so.sendwf(cardidx,path,'.wav',44100,channel=0)
# time.sleep(1)
# so.sendwf(cardidx,path,'.wav',44100,channel=1)


if __name__ == "__main__":
    ## Settings (temporary as these will be queried from GUI)
    import sys
    if len(sys.argv) <= 1:
        raise(Exception('No configuration file passed'))
    else:
        cfpath = sys.argv[1]

    # parse the config file
    controller, box = bc.parse_config(cfpath)
    # # run the box
    time.sleep(2)
    box.select_screen(0)
    box.play_sound('sounds/beep.wav', channel=0)
    box.play_video('video/comet.mpg')
    time.sleep(5)
    box.stop_video()

    time.sleep(5)
    box.select_screen(1)
    box.play_sound('sounds/beep.wav', channel=1)
    box.play_video('video/comet.mpg')
    time.sleep(5)
    box.stop_video()
