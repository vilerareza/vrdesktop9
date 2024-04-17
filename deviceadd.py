import requests
import socket
import pickle
import time

from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.floatlayout import FloatLayout

Builder.load_file("deviceadd.kv")


class DeviceAdd(FloatLayout):
    
    titleLabelText = 'Add New Camera'
    titleLabel = ObjectProperty(None)
    lbl_name = ObjectProperty(None)
    txt_name = ObjectProperty(None)
    lbl_stream_url = ObjectProperty(None)
    txt_stream_url = ObjectProperty(None)
    lbl_desc = ObjectProperty(None)
    txt_desc = ObjectProperty(None)
    btn_add = ObjectProperty(None)
    btn_cancel = ObjectProperty(None)
    sw_enable = ObjectProperty(None)


    def __init__(self, 
                 caller,
                 server_address_file='data/serveraddress.p', 
                 qr_save_dir ='images/temp/qr/', 
                 **kwargs):
        super().__init__(**kwargs)
        # Getting the server adrress
        self.caller = caller
        self.server_address_file = server_address_file
        self.qrSaveDir = qr_save_dir


    def add_new_device(self):
        # Callback function for add device button
        ## Preparing data
        device_name = self.txt_name.text
        stream_url = self.txt_stream_url.text
        device_desc = self.txt_desc.text
        device_enabled = self.sw_enable.active
        ## Get the server IP from the file
        server_address = self.get_server_address()
        ## Create device object in the server'''
        is_success = self.add_to_db(server_address,
                                    device_name, 
                                    stream_url, 
                                    device_desc,
                                    device_enabled)
        if not is_success:
            ## Most likely due to device name is already exist. Highlight the device name text input
            self.txt_name.background_color = (0.9, 0.7, 0.7)
        
        return is_success


    def validate_entry(self, *args):
        isValid = True
        for entry in args:    
            if entry.text == '':
                isValid = False
                entry.background_color = (0.9, 0.7, 0.7)
            else:
                entry.background_color = (1, 1, 1)
        return isValid


    def add_to_db (self, 
                   server_address, 
                   device_name,
                   stream_url, 
                   device_desc,
                   device_enabled):
        
        request_data = {'name': device_name, 
                       'stream_url': stream_url, 
                       'desc': device_desc,
                       'enabled': device_enabled
                       }
        
        print ('Server Address', server_address)
        # Send request to the server
        is_success, r = self.send_request_post(server_address, 
                                               8000, 
                                               'api/device/', 
                                               request_data, 
                                               5)
        print (r.status_code)
        if is_success:
            print (f'Status code: {r.status_code}')
            # Response by status code
            if r.status_code == 201:
                # Refresh the device list.
                self.caller.init_views()
                return True
            else:
                print (f'Name {device_name} already exist. Camera not added')
                return False


    def get_server_address(self):
        # Deserialize server ip and server name from file
        server_address = ''
        try:
            # Load the server hostname:port from file
            with open(self.server_address_file, 'rb') as file:
                server_address = pickle.load(file)
                print ('SERVER ADDRESS', server_address)
        except Exception as e:
            print(f'{e}: Failed loading server address from file: {e}')
        finally:
            return server_address


    def send_request_post(self, 
                          server_address, 
                          port, 
                          url, 
                          data, 
                          timeout = 3):
        '''Send request using server_ip, if it fails try again using server_name'''
        try:
            # Try connecting using IP
            r = requests.post(f'http://{server_address}:{port}/{url}', data = data, timeout = timeout)
            return True, r
        except:
            # Try connecting using server_name           
            for i in range(3):
                try:
                    # Try to get new IP
                    server_address = socket.gethostbyname(server_address)
                    # Try again using new IP
                    r = requests.post(f'http://{server_address}:{port}/{url}', data = data, timeout = timeout)
                    # Save new IP to file
                    self.update_server_addr(server_address)
                    return True, r
                except Exception as e:
                    print (f'{e}: Failed getting server ip. Retry {i+1}...')
                    time.sleep(3)
                    continue
            return False, None


    def update_server_addr(self, server_address):
        # Serialize server ip and server name to file
        try:
            with open(self.server_address_file, 'wb') as file:
                pickle.dump(server_address, file)
        except Exception as e:
            print (f'Saving server address failed: {e}')


    def refresh(self):
        '''Refresh widgets'''
        self.txt_name.text = ''
        self.txt_name.background_color = (1, 1, 1)
        self.txt_stream_url.text = ''
        self.txt_stream_url.background_color = (1, 1, 1)
        self.txt_desc.text = ''
        self.txt_desc.background_color = (1, 1, 1)
        # Enabling the add and cancel button anyway
        self.btn_add.disabled = False
        self.btn_cancel.disabled = False


    def on_parent(self, *args):
        self.refresh()


    def button_press_callback(self, button):
        if button == self.btn_add:
            button.source = 'images/settingview/btn_add_down.png'
        elif button == self.btn_cancel:
            button.source = 'images/settingview/btn_cancel_down.png'


    def button_release_callback(self, button):

        if button == self.btn_add:
            button.source = 'images/settingview/btn_add.png'
            if self.validate_entry(self.txt_name, self.txt_stream_url):
                # Add the new device
                is_success = self.add_new_device()
                if is_success:
                    # Dismissing popup
                    self.caller.device_add_popup.dismiss()

        elif button == self.btn_cancel:
            button.source = 'images/settingview/btn_cancel.png'
            # Dismissing popup
            self.caller.device_add_popup.dismiss()
            
