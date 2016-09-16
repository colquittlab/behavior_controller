
# http://www.fileformat.info/format/mpeg/sample/index.dir
import pygame
import screeninfo
import os
import threading



class PyGamePlayer(object):
	def __init__(self):
		# get secondary monitor size and pos
		monitors = screeninfo.get_monitors()
		if len(monitors)<2:
			raise(Exception('only one monitor connected'))
		self.x = monitors[1].x
		self.y = monitors[1].y
		self.width = monitors[1].width
		self.height = monitors[1].height
		os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (self.x,self.y)
		self.FPS = 60
		pygame.init()
		pygame.mixer.quit()
		self.clock = pygame.time.Clock()
		self.screen = pygame.display.set_mode((self.width,self.height),pygame.NOFRAME)
		self.movie_screen = pygame.Surface(self.screen.get_size()).convert()
		self.movie = None
		self.thread = None
	def play_movie(self,fname):
		# import ipdb; ipdb.set_trace()
		if self.movie is not None:
			self.movie.stop()
		self.movie = pygame.movie.Movie(fname)
		self.movie.set_display(self.movie_screen,self.movie_screen.get_rect())
		self.movie.play()
		playing = True
		while self.movie.get_busy():
		    for event in pygame.event.get():
		        if event.type == pygame.QUIT:
		            self.movie.stop()
		            playing = False

		    self.screen.blit(self.movie_screen,(0,0))
		    pygame.display.update()
		    self.clock.tick(self.FPS)
		self.screen.fill((0,0,0))
		pygame.display.update()

	def send_movie(self, fname):
		if self.thread is not None:
			self.stop()

		self.thread=threading.Thread(target = self.play_movie, args=(fname,))
		self.thread.start()

	def stop(self):
		if self.movie is not None and self.thread is not None:
			self.movie.stop()
			self.thread.join()
		self.screen.fill((0,0,0))
		pygame.display.update()




if __name__=="__main__":
	pgp = PyGamePlayer()
	pgp.send_movie('video/comet.mpg')
	import ipdb; ipdb.set_trace()
