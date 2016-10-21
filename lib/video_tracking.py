import cv as cv
import time as tm
import numpy as np
from multiprocessing import Process
from multiprocessing import Queue
# from threading import Thread
# from Queue import Queue


class Target:

    def __init__(self, camera_idx=0, bounds=None, exclusion_polys=None):
                # set up bounds
             ## initiatite tracking
        self.capture = cv.CaptureFromCAM(camera_idx)
        self.window = None      
        frame = cv.QueryFrame(self.capture)
        
        self.frame_size = cv.GetSize(frame)

        self.bounds = [0]
        if bounds is not None:
            self.bounds.extend(bounds)
        self.bounds.append(self.frame_size[0])

        if exclusion_polys is not None:
            epo = []
            for poly in exclusion_polys:
                polyout = []
                for cordpair in poly:
                    cordout = tuple(cordpair)
                    polyout.append(cordout)
                epo.append(tuple(polyout))
            self.exclusion_polys = epo
        else:
            self.exclusion_polys = None


        self.current_pos = None
        self.current_bin = None
        self.time_of_last_confidence = 0


        self.color_image = cv.CreateImage(cv.GetSize(frame), 8, 3)
        self.grey_image = cv.CreateImage(cv.GetSize(frame), cv.IPL_DEPTH_8U, 1)
        self.moving_average = cv.CreateImage(cv.GetSize(frame), cv.IPL_DEPTH_32F, 3)
        self.temp_image =  cv.CloneImage(self.color_image)       
        self.difference = cv.CloneImage(self.color_image)
        self.find_target(first_frame=True)
  

    def find_target(self, first_frame = False, jump_thresh = 100, dark_thresh = 50): 
        currtime=tm.time()
        self.color_image = cv.QueryFrame(self.capture)
        # Smooth to get rid of false positives
        cv.Smooth(self.color_image, self.color_image, cv.CV_GAUSSIAN, 3, 0)
        grey = cv.CloneImage(self.grey_image)
        cv.CvtColor(self.color_image,grey,cv.CV_RGB2GRAY)
        mean_brightness = np.mean(np.fromstring(grey.tostring(),np.uint8))
        if mean_brightness < dark_thresh:
            loop_time = tm.time()-currtime
            return "dark", loop_time

        if first_frame:
            difference = cv.CloneImage(self.color_image)
            temp = cv.CloneImage(self.color_image)
            cv.ConvertScale(self.color_image, self.moving_average, 1.0, 0.0)
        else:
            cv.RunningAvg(self.color_image, self.moving_average, 0.020, None)

        # Convert the scale of the moving average.
        cv.ConvertScale(self.moving_average, self.temp_image, 1.0, 0.0)

        # Minus the current frame from the moving average.
        cv.AbsDiff(self.color_image, self.temp_image, self.difference)

        # Convert the image to grayscale.
        cv.CvtColor(self.difference, self.grey_image, cv.CV_RGB2GRAY)
        # apply exclusion zones
        if self.exclusion_polys is not None:
            cv.FillPoly(self.grey_image,self.exclusion_polys,(0,))
            # cv.Rectangle(self.grey_image,(zone[0],zone[1]),(zone[2],zone[3])), (255,))
            # cv.ShowImage("Target",self.grey_image)
            pass
        # Convert the image to black and white.
        cv.Threshold(self.grey_image, self.grey_image, 40, 255, cv.CV_THRESH_BINARY)


        # Dilate and erode to get blobs
        cv.Dilate(self.grey_image, self.grey_image, None, 18)
        cv.Erode(self.grey_image, self.grey_image, None, 10)

        storage = cv.CreateMemStorage(0)
        contour = cv.FindContours(self.grey_image, storage, cv.CV_RETR_CCOMP, cv.CV_CHAIN_APPROX_SIMPLE)
        points = []

        while contour:
            bound_rect = cv.BoundingRect(list(contour))
            contour = contour.h_next()

            pt1 = (bound_rect[0], bound_rect[1])
            pt2 = (bound_rect[0] + bound_rect[2], bound_rect[1] + bound_rect[3])
            points.append(pt1)
            points.append(pt2)
            # cv.Rectangle(self.color_image, pt1, pt2, cv.CV_RGB(255,0,0), 1)
        # import ipdb; ipdb.set_trace()
        if len(points):
            center_point = reduce(lambda a, b: ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), points)
        else: 
            center_point = None
        
        if center_point is not None and self.current_pos is not None:
            distance_since_last = np.sqrt(np.dot(np.array(center_point)-np.array(self.current_pos),np.array(center_point)-np.array(self.current_pos)))
        else:
	    distance_since_last = 0
        if distance_since_last > jump_thresh:
            if tm.time() - self.time_of_last_confidence > 2:
                self.time_of_last_confidence = tm.time()
                pass 
            else:
                center_point = self.current_pos
        else:
            self.time_of_last_confidence = tm.time()
           
        
        c = cv.WaitKey(7) % 0x100
        loop_time = tm.time()-currtime
	return center_point, loop_time

    def find_bin_of_pos(self, pos):
        if self.bounds is not None and pos is not None:
            oc, bins = np.histogram([pos[0]], bins = self.bounds)
            return int(np.argmax(oc))
        else:
            return None


    def plot(self):
        if self.window is None:
            self.window=cv.NamedWindow("Target", 1)  
        if self.current_pos is not None:
            cv.Circle(self.color_image, self.current_pos, 40, cv.CV_RGB(255, 255, 255), 1)
            cv.Circle(self.color_image, self.current_pos, 30, cv.CV_RGB(255, 100, 0), 1)
            cv.Circle(self.color_image, self.current_pos, 20, cv.CV_RGB(255, 255, 255), 1)
            cv.Circle(self.color_image, self.current_pos, 10, cv.CV_RGB(255, 100, 0), 1)
            
        if self.bounds is not None:
            for bound in self.bounds:
                cv.Line(self.color_image,(bound,0), (bound,self.frame_size[1]),(255,0,0),5)
        if self.exclusion_polys is not None:
            cv.FillPoly(self.color_image,self.exclusion_polys,(0,))
        # cv.Copy(self.color_im,self.grey_image)
        cv.ShowImage("Target", self.color_image)
        # import ipdb; ipdb.set_trace()


    def run(self, event_queue=None, plot = True, log_period = 1):
        last_log_time = tm.time()
        self.find_target(first_frame=True)
        while True:
            tm.sleep(0.01)
	    
	   
            center_point, loop_time  = self.find_target()
            if center_point is not None:
                if center_point is "dark":
                    center_point = None
                    new_bin = -1
                else:
                    new_bin = self.find_bin_of_pos(center_point)
                self.current_pos = center_point
                
                if new_bin != self.current_bin: 
                    self.current_bin = new_bin
                    # log as event
                    if event_queue != None:
                        event_queue.put((tm.time(), "enter_bin", new_bin))
                    else:
                        print "bird entered bin %d" % new_bin
            if tm.time() > last_log_time + log_period:
                last_log_time = tm.time()
                if event_queue != None:
                    event_queue.put((tm.time(),'pos',self.current_pos, self.find_bin_of_pos(self.current_pos)))
                else:
                    print "current pos ", self.current_pos, ' loop time ', loop_time

            if plot:
                self.plot()
            

def run_tracking_process(bounds = [250, 450], event_queue = None, plot = True, log_period = 1, camera_idx = 0, exclusion_polys = [((120,340), (160,310), (160,240),(120,240)), ((480,310), (520,340), (520,240),(480,240))]):
    t = Target(bounds = bounds, camera_idx = camera_idx, exclusion_polys=exclusion_polys)
    t.run(event_queue=event_queue, plot=plot, log_period = log_period)
    pass

def start_tracking(**args):
    q = Queue()
    args['event_queue']=q
    p=Process(target=run_tracking_process, kwargs=args)
    # p=Thread(target=run_tracking_process, kwargs=args)
    p.start()
    return p, q
    # p.join()

if __name__=="__main__":
    ps = []
    qs = []
    for k in range(0,2):
        p,q=start_tracking(camera_idx=k, plot=False, log_period=.5)
        ps.append(p)
        qs.append(q)
    while True:
     #    # import ipdb; ipdb.set_trace()
     for k in range(0,len(qs)):
        if not qs[k].empty():
            print 'camera', k, ': ', qs[k].get_nowait(), tm.time()
      #   if not q.empty():
       ##      print q.get_nowait(), tm.time()

 
    #run_tracking_process(camera_idx=0, plot=False, log_period=.5)
    # import cProfile
    # command = """run_tracking_process(camera_idx=0, plot=False, log_period=.1)"""
    # cProfile.runctx(command, globals(), locals(), filename='test.profile')
    #p, q = start_tracking(plot=False, log_period = .1)
    
    #while True:
     #    # import ipdb; ipdb.set_trace()
      #   if not q.empty():
       ##      print q.get_nowait(), tm.time()
