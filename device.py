import time
from threading import Thread, Condition
import cv2 as cv
from videocapture import VideoCapture


class Device():

    stream_capture = None
    frame = None

    def __init__(self, 
                 device_id, 
                 name, 
                 stream_url,
                 desc, 
                 enabled,
                 flip,
                 t_timeout = 10,
                 **kwargs):
        
        super().__init__(**kwargs)
        self.device_id = device_id
        self.name = name
        self.stream_url = stream_url
        self.desc = desc
        self.enabled = enabled
        self.flip = flip
        if len(name) > 12:
            self.display_name = f'{name[:12]}...'
        else:
            self.display_name = name
        self.t_timeout = t_timeout
        # Video capture timeout watcher
        self.start_timeout_watcher = Condition()
        # frame condition
        self.frame_condition = Condition()


    def update_device(self, updated_device_data):
        self.name = updated_device_data['name']
        self.stream_url = updated_device_data['stream_url']
        self.desc = updated_device_data['desc']
        self.enabled = updated_device_data['enabled']
        self.flip = updated_device_data['flip']
        if len(self.name) > 12:
            self.display_name = f'{self.name[:12]}...'
        else:
            self.display_name = self.name


    def start_stream(self):

        # Reset the stop flag
        self.stop_flag=False
        
        def start():
        
            # Evaluate the stream_url
            try:
                # Stream url is integer
                stream_url = eval(self.stream_url)
            except:
                # Stream url is sring
                stream_url = self.stream_url
            
            # Stream object is about to be created. Notify the watcher
            with self.start_timeout_watcher:
                self.start_timeout_watcher.notify_all()

            # Create video capture object
            self.stream_capture = VideoCapture(stream_url)
            
            # Capture object created. Notify the watcher again
            with self.start_timeout_watcher:
                self.start_timeout_watcher.notify_all()

            while (not self.stop_flag):

                # Frame capture loop
                is_success, self.frame = self.stream_capture.read()
                if is_success:
                    ## Frame processing
                    if not self.flip:
                        ### flip logic is reversed. MAybe due to the texture.
                        self.frame = cv.flip(self.frame,0)
                    ### BGR to RGB
                    self.frame = self.frame[:,:,::-1]
                    with self.frame_condition:
                        self.frame_condition.notify_all()

            ## Loop ended. Stop the stream capture object
            self.stream_capture.stop_flag = True
            self.stream_capture = None
            print ('Done', self.name, self.stream_url)

        # Starting the stream
        t = Thread(target = start)
        t.daemon = True
        t.start()
        
        # Monitor the video capture creation timeout
        with self.start_timeout_watcher:
            if not (self.start_timeout_watcher.wait(timeout = self.t_timeout)):                
                # Dont retrieve any frame
                self.stop_stream()
                # Notify all waiting widgets
                self.start_timeout_watcher.notify_all()


    def stop_stream(self):
        # The checker will be stop at max self.t_check
        self.stop_flag=True


    def restart_stream(self, delay=5):
        self.stop_stream()
        # Put some delay before starting again to make sure the existing thread stop first.
        time.sleep(delay)
        # Start the stream again
        self.start_stream()
