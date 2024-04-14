import threading
import socket
import time
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty
from kivy.lang import Builder
from kivy.clock import Clock

Builder.load_file('deviceIcon.kv')


class DeviceIcon(ButtonBehavior, FloatLayout):

    device_name = StringProperty("")
    stream_url = StringProperty("")
    device_enabled = BooleanProperty(True)

    statusImage = ObjectProperty(None)
    deviceLabel = ObjectProperty(None)
    t_status_checker = None
    stop_flag = False
    stream_url = ''
    tCheck = 3
    isConnected = False


    def __init__(self, 
                 device_name, 
                 stream_url,
                 device_enabled,
                 **kwargs):
        super().__init__(**kwargs)
        
        self.device_name = device_name
        self.stream_url = stream_url
        self.device_enabled = device_enabled
        self.disabled = True


    def ping_device(self):

        '''ping device to check the connectivity'''

        def callback_ok(*args):
            # Enable the item
            self.disabled = False
            self.isConnected = True
            self.statusImage.source = "images/multiview/standby.png"
            self.deviceLabel.text = "[color=cccccc]"+self.device_name+"[/color]"
        
        def callback_fail(*args):
            # Disable the item
            self.disabled = False
            self.isConnected = False
            self.statusImage.source = "images/multiview/unavailable.png"
            self.deviceLabel.text = "[color=777777]"+self.device_name+"[/color]"

        def _ping_device(): 
            
            for i in range(3):
                if not self.stop_flag:
                # Perform 3 times trial
                    try:
                        time.sleep(3)
                        '''ping here'''
                        pass
                        break
                    except Exception as e:
                        print (f'{e}: Failed getting server ip. Retry {i+1}...')
                        continue
            if self.stream_url != '':
                Clock.schedule_once(callback_ok, 0)
            else:
                Clock.schedule_once(callback_fail, 0)

        self.disabled = True
        self.statusImage.source = "images/multiview/connecting.png"
        t_get_device_ip = threading.Thread(target = _ping_device)
        t_get_device_ip.daemon = True
        t_get_device_ip.start()

    def stop(self):
        self.stop_flag=True
