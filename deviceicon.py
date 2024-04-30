import threading
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
    device_flip = BooleanProperty(True)

    statusImage = ObjectProperty(None)
    deviceLabel = ObjectProperty(None)
    t_status_checker = None
    stop_flag = False
    stream_url = ''
    tCheck = 3
    is_connected = False
    disabled = True


    def __init__(self, 
                 device,
                 **kwargs):
        super().__init__(**kwargs)
        
        self.device = device
        self.wait_device_start()


    def wait_device_start(self):
        # Wait for the device to start

        def callback_ok(*args):
            # Enable the item
            self.disabled = False
            self.is_connected = True
            self.statusImage.source = "images/multiview/standby.png"
            self.deviceLabel.text = "[color=cccccc]"+self.device.name+"[/color]"
        
        def callback_fail(*args):
            # Disable the item
            self.disabled = False
            self.is_connected = False
            self.statusImage.source = "images/multiview/unavailable.png"
            self.deviceLabel.text = "[color=777777]"+self.device.name+"[/color]"

        def check(): 

            with self.device.start_timeout_watcher:
                # Wait for starting
                self.device.start_timeout_watcher.wait()
                # print ('notified', self.device.timeout_watcher)
                # Device is starting. Wait until timeout
                if self.device.start_timeout_watcher.wait():
                    if not self.device.stop_flag:
                        # Device started OK
                        Clock.schedule_once(callback_ok, 0)
                    else:
                        # timeout
                        Clock.schedule_once(callback_fail, 0)

        t_get_device_ip = threading.Thread(target = check)
        t_get_device_ip.daemon = True
        t_get_device_ip.start()


    def stop(self):
        self.stop_flag=True
