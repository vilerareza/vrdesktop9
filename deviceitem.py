import pickle
import requests
import socket
import time

from kivy.lang import Builder
from kivy.graphics import Color, Rectangle
from kivy.properties import NumericProperty, ObjectProperty, StringProperty, BooleanProperty
from kivy.uix.floatlayout import FloatLayout
from mylayoutwidgets import ColorLabel
from mylayoutwidgets import ImageButton

Builder.load_file("deviceitem.kv")


class DeviceItem(FloatLayout):

    setting_view = ObjectProperty(None)
    device_id = NumericProperty(0)
    name = StringProperty("")
    stream_url = ''
    desc = ''
    enabled = BooleanProperty(True)
    image = ObjectProperty(None)
    label = ObjectProperty(None)
    btn_edit = ObjectProperty(None)
    btn_delete = ObjectProperty(None)
    
    imagePath = "images/settingview/device_item.png"

    def __init__(self, 
                 device_id, 
                 name, 
                 stream_url, 
                 desc, 
                 enabled,
                 server_address_file='data/serveraddress.p',
                 server_port = 8000, 
                 **kwargs):
        
        super().__init__(**kwargs)
        self.padding = [0]
        self.device_id = device_id
        self.name = name
        self.stream_url = stream_url
        self.desc = desc
        self.enabled = enabled
        self.server_address_file = server_address_file
        self.server_port = server_port


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


    def delete_device(self, delete_api = 'api/device' ):
        try:
            server_address = self.get_server_address()
            isSuccess, r = self.send_request('delete', 
                                             server_address, 
                                             8000, 
                                             f'{delete_api}/{self.device_id}/', 
                                             None, 
                                             5)
            if isSuccess:
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
