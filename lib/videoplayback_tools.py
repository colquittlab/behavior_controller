
# http://www.fileformat.info/format/mpeg/sample/index.dir
import pygame
import screeninfo
import os
import threading
from pygame.locals import *
import cv2
import numpy


# def initCamera(camera_idx=0):
#     camera=cv2.VideoCapture(camera_idx)
#     camera.set(3,640)
#     camera.set(4,480)
#     return camera

def openVideo(fname):
    cap = cv2.VideoCapture(fname)
    fps = cap.get(5) # fps is int property 5
    return cap, fps

def cvtFrame(frame, color=True, res_out=(100,100), rotation=0):
    frame=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
    if not color:
        frame=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
        frame=cv2.cvtColor(frame,cv2.COLOR_GRAY2RGB)
    frame=rotateFrame(frame, rotation)
    frame=cv2.resize(frame, res_out, interpolation = cv2.INTER_AREA)
    frame=numpy.rot90(frame)
    frame=pygame.surfarray.make_surface(frame)
    return frame

def rotateFrame(frame, rotation):
    if rotation==1:
        frame = cv2.transpose(frame)
    elif rotation==2:
        frame = cv2.flip(frame,0)
    elif rotation==3:
        frame=cv2.flip(cv2.transpose(frame),1)
    else:
        pass
    return frame


class PyGamePlayer(object):
    def __init__(self):
        # get secondary monitor size and pos
        monitors = screeninfo.get_monitors()
        if len(monitors)<2:
            # raise(Exception('only one monior connected'))
            self.x=0
            self.y=0
            self.width=800
            self.height=800
        else:
            self.x = monitors[1].x
            self.y = monitors[1].y
            self.width = monitors[1].width
            self.height = monitors[1].height
        os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (self.x,self.y)
        pygame.init()
        pygame.mixer.quit()

        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((self.width,self.height),pygame.NOFRAME)
        self.screen.fill((0,0,0))
        pygame.display.update()
        # self.movie_screen = pygame.Surface(self.screen.get_size()).convert()
        # self.movie = None
        self.playing = False
        self.thread = None
    def play_movie(self,fname,rotation=1):
        # import ipdb; ipdb.set_trace()
        if self.playing:
            self.stop()

        mov, fps = openVideo(fname)
        self.playing=True
        while self.playing:
            retval,frame=mov.read()
            if frame is not None:
                frame=cvtFrame(frame, res_out = (self.width, self.height), rotation=rotation)
                self.screen.blit(frame,(0,0))
                pygame.display.flip()
                cv2.waitKey(int(float(1000)/fps))
            else:
                self.playing=False
            # 
        cv2.destroyAllWindows()
        self.screen.fill((0,0,0))
        pygame.display.update()

    def send_movie(self, *args, **kwargs):
        if self.thread is not None:
            self.stop()
        self.thread=threading.Thread(target = self.play_movie, args=args, kwargs=kwargs)
        self.thread.start()

    def stop(self):
        if self.thread is not None:
            self.playing = False
            self.thread.join()
        cv2.destroyAllWindows()
        self.screen.fill((0,0,0))
        pygame.display.update()




if __name__=="__main__":
    pgp = PyGamePlayer()
    # pgp.send_movie('video/jeffbird.mpg')
    import ipdb; ipdb.set_trace()
