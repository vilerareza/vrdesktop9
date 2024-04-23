import pickle
import requests
import socket
import time
from functools import partial
from threading import Thread, Condition

from kivy.lang import Builder
from kivy.graphics.texture import Texture
from kivy.properties import NumericProperty, ObjectProperty, StringProperty, BooleanProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
from mylayoutwidgets import ColorLabel
from mylayoutwidgets import ImageButton

import cv2 as cv
from videocapture import VideoCapture

Builder.load_file("deviceitem.kv")


class DeviceItem(FloatLayout):

    setting_view = ObjectProperty(None)
    device_id = NumericProperty(0)
    display_name = StringProperty("")
    stream_url = StringProperty("")
    desc = StringProperty("")
    enabled = BooleanProperty(True)
    flip = BooleanProperty(False)
    bg_img = ObjectProperty(None)
    img_icon = ObjectProperty(None)
    lbl_name = ObjectProperty(None)
    btn_edit = ObjectProperty(None)
    btn_delete = ObjectProperty(None)
    stop_flag = False
    is_check_running = False
    stream_capture = None
    
    # bg_img_path = "images/settingview/device_item.png"

    def __init__(self, 
                 device_id, 
                 name, 
                 stream_url,
                 desc, 
                 enabled,
                 flip,
                 server_address_file='data/serveraddress.p',
                 server_port = 8000, 
                 t_check = 5,
                 **kwargs):
        
        super().__init__(**kwargs)
        self.padding = [0]
        self.device_id = device_id
        self.name = name
        self.stream_url = stream_url
        self.desc = desc
        self.enabled = enabled
        self.flip = flip
        self.server_address_file = server_address_file
        self.server_port = server_port
        if len(name) > 12:
            self.display_name = f'{name[:12]}...'
        else:
            self.display_name = name
        self.t_check = t_check


    def get_server_address(self):
        # Deserialize server ip and server name from file
        server_address = ''
        try:
            # Load the server hostname:port from file
            with open(self.server_address_file, 'rb') as file:
                server_address = pickle.load(file)
        except Exception as e:
            print(f'{e}: Failed loading server address from file: {e}')
        finally:
            return server_address


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
        # Restart the device checker in new thread
        t_device_check = Thread(target = self.restart_checker)
        t_device_check.daemon = True
        t_device_check.start()


    def delete_device(self, delete_api = 'api/device'):
        try:
            server_address = self.get_server_address()
            isSuccess, r = self.send_request('delete', 
                                             server_address, 
                                             8000, 
                                             f'{delete_api}/{self.device_id}/', 
                                             None, 
                                             5)
            if isSuccess:
                # Stop this device
                self.stop_flag = True
                print (f'Status code: {r.status_code}')
                # Refresh the device list.
                self.setting_view.init_views()
        except Exception as e:
            print (e)


    def send_request(self, method, server_address, port, url, data = None, timeout = 3):
        '''Send request using server_ip, if it fails try again using server_name'''
        try:
            # Try connecting using IP
            if method ==  'get':
                # GET
                r = requests.get(f'http://{server_address}:{port}/{url}', timeout = timeout)
            elif method == 'post':
                # POST
                r = requests.post(f'http://{server_address}:{port}/{url}', data = data, timeout = timeout)
            elif method == 'put':
                # PUT
                r = requests.put(f'http://{server_address}:{port}/{url}', data = data, timeout = timeout)
            elif method == 'delete':
                # DELETE
                r = requests.delete(f'http://{server_address}:{port}/{url}', timeout = timeout)
            return True, r
        
        except:
            # Server IP maybe already changed. Try to find the new IP using server_name           
            for i in range(3):
                try:
                    # Try to get new IP
                    server_address = socket.gethostbyname(server_address)
                    # Try again using new IP
                    if method ==  'get':
                        # GET
                        r = requests.get(f'http://{server_address}:{port}/{url}', timeout = timeout)
                    elif method == 'post':
                        # POST
                        r = requests.post(f'http://{server_address}:{port}/{url}', data = data, timeout = timeout)
                    elif method == 'put':
                        # PUT
                        r = requests.put(f'http://{server_address}:{port}/{url}', data = data, timeout = timeout)
                    elif method == 'delete':
                        # DELETE
                        r = requests.delete(f'http://{server_address}:{port}/{url}', timeout = timeout)
                    # Save new IP to file
                    self.update_server_addr(server_address)
                    return True, r
                except Exception as e:
                    print (f'{e}: Failed getting server ip. Retry {i+1}...')
                    time.sleep(3)
                    continue
            return False, None


    def start_device_checker(self):

        # Start the status checker thread
        self.stop_flag=False
        # video capture timeout watcher
        timeout_watcher = Condition()
        # Initial texture creation
        ## Initiate frame_size with size of img_icon widget
        self.frame_size = [int(self.img_icon.size[0]), int(self.img_icon.size[1])]
        self.img_icon.texture = Texture.create(size=self.frame_size, colorfmt="rgb")
        
        # Update the livestream texture with new frame
        def update_frame(buff, *largs):
            data = buff.flatten()
            self.img_icon.texture.blit_buffer(data, bufferfmt="ubyte", colorfmt="rgb")
            self.img_icon.canvas.ask_update()

        # Update the livestream texture with new frame
        def on_frame_(img_array):
            Clock.schedule_once(partial(update_frame, img_array), 0)

        def callback_ok(*args):
            print ('Device OK')
            on_frame_(args[0])
        
        def callback_fail(*args):
            print ('Fail to get frame')

        def check():
        
            # Evaluate the stream_url
            try:
                # Stream url is integer
                stream_url = eval(self.stream_url)
            except:
                # Stream url is sring
                stream_url = self.stream_url
            
            # Create video capture object
            self.stream_capture = VideoCapture(stream_url)
            
            # Capture object created. Notify the watcher
            with timeout_watcher:
                timeout_watcher.notify_all()
            
            while (not self.stop_flag):
                # Frame capture loop

                is_success, frame = self.stream_capture.read()

                if is_success:
                    
                    # Compare the received frame size with current texture. If different, adjust the size of the texture
                    if (frame.shape[1], frame.shape[0]) != (self.frame_size[0], self.frame_size[1]):
                        self.img_icon.texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt="rgb")
                        # Remember the frame size
                        self.frame_size[0] = frame.shape[1]
                        self.frame_size[1] = frame.shape[0]

                    ## Frame processing
                    if not self.flip:
                        ### flip logic is reversed. MAybe due to the texture.
                        frame = cv.flip(frame,0)
                    frame = frame[:,:,::-1]
                    Clock.schedule_once(partial(callback_ok, frame), 0)

                else:
                    ## Connection failed
                    Clock.schedule_once(callback_fail, 0)

                ## Delay between check
                time.sleep(self.t_check)

            ## Loop ended. Stop the stream capture object
            self.stream_capture.stop_flag = True
            self.stream_capture = None
            print ('Done', self.stream_url)

        # Starting the server checker thread
        t = Thread(target = check)
        t.daemon = True
        t.start()
        
        # Monitor the video capture creation timeout
        with timeout_watcher:
            if not (timeout_watcher.wait(timeout = 10)):
                # Dont retrieve any frame
                self.stop_checker()
                print ('timeout')


    def stop_checker(self):
        # The checker will be stop at max self.t_check
        self.stop_flag=True


    def restart_checker(self):
        self.stop_checker()
        # Put some delay before starting again to make sure the existing thread stop first.
        time.sleep(self.t_check)
        # Re-initiate device checker in new thread (so that any open popup can just dismiss immediately).
        self.start_device_checker()
        

    def button_press_callback(self, button):
        if button == self.btn_edit:
            button.source =  'images/settingview/btn_edit_device_down.png'
        if button == self.btn_delete:
            button.source =  'images/settingview/btn_delete_down.png'


    def button_release_callback(self, button):

        if button == self.btn_edit:
            # Open the device setting popup
            button.source = 'images/settingview/btn_edit_device.png'
            self.setting_view.open_popup(self)
        if button == self.btn_delete:
            # Delete this device from db
            button.source =  'images/settingview/btn_delete.png'
            self.delete_device()
