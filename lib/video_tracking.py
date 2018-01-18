import cv as cv
import cv2
import time as tm
import numpy as np
from multiprocessing import Process
from multiprocessing import Queue
import cPickle as pickle
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
        self.raw_image = cv.CreateImage(cv.GetSize(frame), 8, 3)
        self.color_image = cv.CreateImage(cv.GetSize(frame), 8, 3)
        self.grey_image = cv.CreateImage(cv.GetSize(frame), cv.IPL_DEPTH_8U, 1)
        self.moving_average = cv.CreateImage(cv.GetSize(frame), cv.IPL_DEPTH_32F, 3)
        self.temp_image =  cv.CloneImage(self.color_image)       
        self.difference = cv.CloneImage(self.color_image)
        self.color_image= cv.QueryFrame(self.capture)
        self.find_target(first_frame=True)

        self.codec = cv.CV_FOURCC('D','I','V','X') # MPEG-4 
        self.size = cv.GetSize(frame)
        self.writing = False
        self.writer = None
        self.fps = None

    def detect_fps(self, ncap = 100):
        if self.capture is not None:
            count = 0; 
            times = np.ndarray(ncap+1)
            while count < 30:
                count += 1
                cv.QueryFrame(self.capture)
            count = 0
            start = tm.time()
            times[count]=start
            while count < ncap:
                count +=1 
                cv.QueryFrame(self.capture)
                times[count] = tm.time()
                tm.sleep(0.001)
            end = times[count]
            self.fps = np.round(float(count-1) / (end-times[1]))
            print 'FPS',self.fps



    def start_writing(self, fname):
        fname = fname.replace("//","/")
        fname = fname.replace(".","p")
        fname = "%s.avi" % fname
        self.writer = cv.CreateVideoWriter(
            fname,     # Filename
            self.codec,                              # Codec for compression
            int(self.fps),                                 # Frames per second
            self.size,                         # Width / Height tuple
            True                                # Color flag
        )
        self.writing = True

        return fname

    def stop_writing(self, filename, video_start_time, video_stop_time, nframes):
        del(self.writer)
        self.writer = None
        self.writing=False
        file = open("%s.videoinfo" % filename, 'w')
        file.write("Video file information for %s\n " % filename)
        file.write("start_time=%f\n" % video_start_time)
        file.write("stop_time=%f\n" % video_stop_time )
        file.write("nframes=%d\n" % nframes)
        file.write("length(s)= %f\n" % (video_stop_time-video_start_time))
        file.write("fps = %0.2f\n" % (float(nframes)/(video_stop_time-video_start_time)))
        file.close()

        pass


    def find_target(self, first_frame = False, jump_thresh = 100, dark_thresh = 50): 
        currtime=tm.time()
        # self.color_image = new_frame
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
           
        
        # c = cv.WaitKey(7) % 0x100
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

    def get_image_from_buffer(self, q):
        q.get(block=True)
        new_frame = pickle.loads(q.get(block=True))
        new_image = cv.CreateImageHeader(self.frame_size, 8, 3)
        cv.SetData(new_image, new_frame)
        self.color_image = new_image
        return new_image

    def run_capture(self, event_q = None, frame_q=None, control_q=None):
        filename = ""
        frame  = cv.CreateImage(self.frame_size, 8, 3)
        frame = cv.QueryFrame(self.capture)
        last = tm.time()
        count = 0
        frame_count=0
        start_time = tm.time()
        now=start_time
        video_start_time = now
        video_stop_time = now
        self.detect_fps()

        while True:
            count+=1
            then = tm.time()
            frame = cv.QueryFrame(self.capture)
            last=now
            now=tm.time()
            # print now-last, now-then
            if not frame_q.full():
                frame_q.put(pickle.dumps(frame.tostring(),-1), block=True)
            now=tm.time()
            if self.writing:
                cv.WriteFrame(self.writer,frame)
                frame_count +=1
                video_frame_count +=1
                if not control_q.empty():
                    command = control_q.get(block=True)
                    if command[0]=="stop":
                        video_stop_time = tm.time()
                        self.stop_writing(filename, video_start_time, video_stop_time, video_frame_count)
                        event_q.put((video_stop_time, "Stopped video recording: %s  --- %0.1fs, %d frames, %0.1f FPS" % (filename, np.round(video_stop_time - video_start_time), video_frame_count, (video_frame_count / (video_stop_time - video_start_time)))))
                        
                    elif command[0]=="start":
                        video_stop_time = tm.time()
                        self.stop_writing(filename, video_start_time, video_stop_time, video_frame_count)
                        event_q.put((video_stop_time, "Stopped video recording: %s  --- %0.1fs, %d frames, %0.1f FPS" % (filename, np.round(video_stop_time - video_start_time), video_frame_count, (video_frame_count / (video_stop_time - video_start_time)))))
                        filename=self.start_writing(command[1])
                        video_start_time = tm.time()
                        video_frame_count = 0
                        event_q.put((video_start_time, "Started video recording: %s" % filename))       
            else:
                if not control_q.empty():
                    command = control_q.get(block=True)
                    if command[0]=="start":
                        filename=self.start_writing(command[1])
                        video_start_time = tm.time()
                        video_frame_count = 0
                        event_q.put((video_start_time, "Started video recording: %s" % filename))
            tm.sleep(0.001)
                # print "frames written", frame_count, now-start_time

            # print "capt", count, now-last#, float(count)/(now-start_time)
            
        print "cap done"



    def run(self, event_q=None, frame_q=None, plot = True, log_period = 1):
        last_log_time = tm.time()
        # while True:
        #     print frame_q.qsize()

        
        self.get_image_from_buffer(frame_q)
        # self.color_image = new_frame
        # import ipdb; ipdb.set_trace()
        center_point, loop_time = self.find_target(first_frame=True)


        # print new_frame
        last = tm.time()
        start_time = tm.time()
        while True:
            now = tm.time()
            last = now
            self.get_image_from_buffer(frame_q)
            center_point, loop_time = self.find_target()
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
                    if event_q != None:
                        event_q.put((tm.time(), "enter_bin", new_bin))
                    else:
                        print "bird entered bin %d" % new_bin
            if tm.time() > last_log_time + log_period:
                last_log_time = tm.time()
                if event_q != None:
                    event_q.put((tm.time(),'pos',self.current_pos, self.find_bin_of_pos(self.current_pos)))
                else:
                    print "current pos ", self.current_pos, ' loop time ', loop_time


            if plot:
                self.plot()
                c = cv.WaitKey(7) % 0x100

def run_capture_process(t = None, event_q = None, frame_q=None, control_q = None, plot=False, log_period=1):
    t.run_capture(event_q = event_q, frame_q = frame_q, control_q = control_q)
    pass


def run_tracking_process(t = None, event_q = None, frame_q = None, plot=False, control_q = None, log_period=1):
    t.run(event_q=event_q, frame_q= frame_q, plot=plot, log_period = log_period)
    pass

def start_tracking(bounds = [250, 450], event_q = None, control_q=None, plot = True, log_period = 1, camera_idx = 0, exclusion_polys = [((120,340), (160,310), (160,240),(120,240)), ((480,310), (520,340), (520,240),(480,240))]):
    t = Target(bounds = bounds, camera_idx = camera_idx, exclusion_polys=exclusion_polys)
    if event_q is None:
        event_q = Queue()
    if control_q is None:
        control_q = Queue(maxsize=10)


    frame_q = Queue(maxsize=1)
    args={}
    args['event_q']=event_q
    args['frame_q'] = frame_q
    args['control_q'] = control_q
    args['t']=t
    args['plot'] = plot
    args['log_period'] = log_period

    p_cap=Process(target=run_capture_process, kwargs=args)
    p_cap.start()
    # run_capture_process(**args)
    p_track=Process(target=run_tracking_process, kwargs=args)
    p_track.start()
    # run_tracking_process(**args)
    # p=Thread(target=run_tracking_process, kwargs=args)
    return p_cap, p_track, event_q, control_q, t
    # p.join()

def print_event_queue(event_queue):
    while True:
        print event_queue.get(block=True), '\n'


if __name__=="__main__":
    import sys
    if len(sys.argv) > 1:
        camera_idx = int(sys.argv[1])
    else:
        camera_idx=0

    ps = []
    qs = []
    p_cap, p_track ,event_q, control_q, t=start_tracking(camera_idx=camera_idx, plot=True, log_period=2)

    print_process = Process(target = print_event_queue, args = (event_q,))
    print_process.start()

    test_idx = 0 
    while True:
        test_idx +=1
        video_name = raw_input('\nEnter video name ("test_video_%d"):' % test_idx )
    #     # print video_name
        if video_name == "":
            video_name = 'test_video_%d' % (test_idx)
        control_q.put(('start',video_name))
        raw_input("any key to stop")
        control_q.put(('stop',''))




            
    # import ipdb; ipdb.set_trace()
    # control_q.put(["start","test_video"])
    # ipdb.set_trace()
    # control_q.put(["stop",""])






    #run_tracking_process(camera_idx=0, plot=False, log_period=.5)
    # import cProfile
    # command = """run_tracking_process(camera_idx=0, plot=False, log_period=.1)"""
    # cProfile.runctx(command, globals(), locals(), filename='test.profile')
    #p, q = start_tracking(plot=False, log_period = .1)
    
    #while True:
     #    # import ipdb; ipdb.set_trace()
      #   if not q.empty():
       ##      print q.get_nowait(), tm.time()
