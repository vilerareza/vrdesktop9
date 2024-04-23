import requests
import socket
import pickle
import time
from functools import partial
from threading import Thread

from kivy.lang import Builder
from kivy.properties import ObjectProperty, BooleanProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from mylayoutwidgets import ImageButton, ImageToggle
from kivy.clock import Clock

Builder.load_file("devicesetting.kv")


class DeviceSetting(FloatLayout):

    lbl_name = ObjectProperty(None)
    txt_name = ObjectProperty(None)
    lbl_stream_url = ObjectProperty(None)
    txt_stream_url = ObjectProperty(None)
    lbl_desc = ObjectProperty(None)
    txt_desc = ObjectProperty(None)
    btn_save = ObjectProperty(None)
    btn_cancel = ObjectProperty(None)
    sw_enable = ObjectProperty(None)
    sw_flip = ObjectProperty(None)


    def __init__(self, caller,
                 server_address_file='data/serveraddress.p',
                 **kwargs):
        super().__init__(**kwargs)
        # Getting the server adrress
        self.server_address_file = server_address_file
        self.caller = caller


    def save_device_to_db(self, *args):

        def _send_request():
            # User pressed "Save". Save attribute to selected device
            device_id = self.device_item.device_id
            device_name = self.txt_name.text
            stream_url = self.txt_stream_url.text
            device_desc = self.txt_desc.text
            device_enabled = self.sw_enable.active
            device_flip = self.sw_flip.active
            deviceData = {'name': device_name,
                        'stream_url': stream_url, 
                        'desc': device_desc, 
                        'enabled' : device_enabled,
                        'prev_name': self.prev_device_name,
                        'flip': device_flip}
            server_address = self.get_server_address()
            is_success, r = self.send_request('put', 
                                            server_address,
                                            8000, 
                                            f'api/device/{device_id}/',
                                            deviceData, 
                                            5)
            print (r.status_code)
            # Sending request complete. Run callback function
            Clock.schedule_once(partial(callback, is_success, r, server_address, device_id), 0)

        def callback(is_success, r, server_address, device_id, *args):
            if is_success and r.status_code == 200:
                # Update success
                ## Get the new device attribute (json) form the sever
                updated_device_data = self.get_device_data(server_address, device_id)
                if updated_device_data != {}:
                    self.device_item.update_device(updated_device_data)
            else:
                # Update failed. Most likely due to device name is already exist. Highlight the device name text input
                self.txt_name.background_color = (0.9, 0.7, 0.7)
        
        # Starting the new thread
        t = Thread(target = _send_request)
        t.daemon = True
        t.start()


    def validate_entry(self, *args):
        isValid = True
        for entry in args:
            if entry.text == '':
                isValid = False
                entry.background_color = (0.9, 0.7, 0.7)
            else:
                entry.background_color = (1, 1, 1)
        return isValid


    def get_device_data(self, server_address, device_id):
        '''Get device with specific device ID from server REST API'''
        try:
            _, r = self.send_request('get', server_address, 8000, f'api/device/{device_id}/', None, 5)
            device = r.json()
            return device
        except Exception as e:
            print (e)
            return {}


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


    def update_server_addr(self, server_address):
        # Serialize server ip and server name to file
        try:
            with open(self.server_address_file, 'wb') as file:
                pickle.dump(server_address, file)
        except Exception as e:
            print (f'Saving server address failed: {e}')


    def on_parent(self, *args):
        if self.parent:
            self.reset()


    def reset(self):
        # Reset the widgets state
        self.txt_name.background_color = (1, 1, 1)
        self.txt_stream_url.background_color = (1, 1, 1)
        self.txt_desc.background_color = (1, 1, 1)


    def fill(self, device_item):
        # Fill the widgets with device setting
        self.reset()
        self.device_item = device_item
        self.txt_name.text = device_item.name
        self.txt_stream_url.text = device_item.stream_url
        self.txt_desc.text = device_item.desc
        self.sw_enable.active = device_item.enabled
        self.sw_flip.active = device_item.flip
        ## Save the current name as previous name (for the server to determine if the name has changed)
        self.prev_device_name = device_item.name


    def remove_from_db(self):
        print ('remove from db')
        if self.deviceObjID:
            try:
                serverIP, serverName = self.get_server_address()
                isSuccess, r = self.send_request('delete', serverIP, serverName, 8000, f'api/device/{self.deviceObjID}/', None, 5)
                if isSuccess:
                    print (f'Status code: {r.status_code}')
                    # Refresh the device list.
                    self.parent.reinit_views()
                    self.parent.no_selection_config()
            except Exception as e:
                print (e)


    def button_press_callback(self, button):
        if button == self.btn_save:
            button.source =  'images/settingview/btn_save_server_down.png'
        elif button == self.btn_cancel:
            button.source =  'images/settingview/btn_cancel_down.png'


    def button_release_callback(self, button):
        if button == self.btn_save:
            button.source = 'images/settingview/btn_save_server.png'
            if self.validate_entry(self.txt_name, self.txt_stream_url):
                self.save_device_to_db()
                # Dismissing popup
                #Clock.schedule_once((self.caller.device_setting_popup.dismiss), 0)
                self.caller.device_setting_popup.dismiss()
            
        elif button == self.btn_cancel:
            button.source =  'images/settingview/btn_cancel.png'
            # Dismissing popup
            self.caller.device_setting_popup.dismiss()


