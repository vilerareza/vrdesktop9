import requests
import pickle
import socket
import time
from functools import partial
from threading import Thread

from kivy.lang import Builder
from kivy.properties import ListProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from mylayoutwidgets import ImageButton
from kivy.clock import Clock

from deviceitem import DeviceItem
from devicelist import DeviceList
from serverbox import ServerBox
from serveritem import ServerItem
from devicelistbox import DeviceListBox
from serversetting import ServerSetting
from devicesetting import DeviceSetting
from deviceadd import DeviceAdd

from kivy.uix.popup import Popup

Builder.load_file("settingview.kv")


class SettingView(BoxLayout):

    # Application manager onj
    manager = ObjectProperty(None)
    server_box = ObjectProperty(None)
    devices = ListProperty([])
    deviceList = ObjectProperty(None)
    settingContentBox = ObjectProperty(None)
    lastConnDevFile = 'data/lastconnecteddev.p'
    isServerTimeout = False
    stop_flag = False
    popup_requester = ObjectProperty(None)


    def __init__(self, server_address_file='data/serveraddress.p', **kwargs):
        super(SettingView, self).__init__(**kwargs)
        # Getting the server adrress, deserialize the serveraddress.p
        self.serverAddressFile = server_address_file
        # Server setting popup
        self.server_setting_popup = ServerSettingPopup(caller=self)
        # Device setting popup
        self.device_setting_popup = DeviceSettingPopup(caller=self)
        # Device add popup
        self.device_add_popup = DeviceAddPopup(caller=self)


    def init_views(self, *args):
        '''Initialize the view of this class'''
        # Refresh from previous state
        self.refresh_views()
        # Init devices
        self.init_devices()
        # Start server status checker
        self.start_server_checker()


    def refresh_views(self):
        # Refresh the device list
        self.devices.clear()
        # Clear device list widgets
        self.deviceList.deviceListLayout.clear_widgets()


    def init_devices(self):
        '''Get devices from server and show it on the layout'''
        # Get the server IP from the file
        server_address = self.get_server_address()
        if server_address:
            # Show popup message
            self.manager.open_popup(self)
            # Get devices from the server - perform in new thread
            self.get_devices(server_address = server_address)
        else:
            print ('Unable to get server IP and server name. Nothing to init')


    def get_server_address(self):
        '''Deserialize server ip and server name from file'''
        server_address = ''
        try:
            # Load the server hostname:port from file
            with open(self.serverAddressFile, 'rb') as file:
                server_address = pickle.load(file)
        except Exception as e:
            print(f'{e}: Failed loading server address from file: {e}')
        finally:
            return server_address


    def get_devices(self, server_address):
        
        print ('get devices')
        # Retrieve devices from server REST API

        def _send_request():
            '''Thread function'''
            # Resetting the stop flag
            self.stop_flag = False
            # Send request to the server
            isSuccess, r = self.send_request(server_address, 8000, 'api/device/', 5)
            # Sending request complete. Run callback function
            Clock.schedule_once(partial(callback, isSuccess, r), 0)

        def callback(isSuccess, r, *args):
            if isSuccess:
                devices_response = r.json()  # Produce list of dict
                for device_response in devices_response:
                    device_id = device_response['id']
                    name = device_response['name']
                    stream_url = device_response['stream_url']
                    desc = device_response['desc']
                    enabled = device_response['enabled']
                    flip = device_response['flip']
                    # Appending received devices to devices property
                    device =  DeviceItem(device_id = device_id,
                                         name = name,
                                         stream_url = stream_url,
                                         desc = desc,
                                         enabled = enabled,
                                         flip = flip,
                                         setting_view = self)
                    self.devices.append(device)
                # Storing connected devices into the file
                self.store_connected_device(deviceJSON = devices_response)
                # Display devices
                self.populate_items_to_list(self.devices)
                # Dismissing popup message
                self.manager.popup.dismiss()
                
                # Initiate device checker in new thread
                t_device_check = Thread(target = self.start_devices_checker)
                t_device_check.daemon = True
                t_device_check.start()

            else:
                if self.stop_flag:
                    # Triggered by cancellation
                    # Dismissing popup message
                    self.manager.popup.dismiss()
                    # Clearing stop flag
                    self.stop_flag = False
                else:
                    # Timeout. Prompting user to acknowledge
                    self.isServerTimeout = True
                    self.manager.popup.title = 'Server connection timeout'
                    self.manager.popup.button.text = 'OK'
                    print ('Get devices timeout')

        # Starting the new thread
        t = Thread(target = _send_request)
        t.daemon = True
        t.start()


    def send_request(self, server_address, port, url, timeout = 3):
        '''Send request using server_ip, if it fails try again using server_name'''
        try:
            # Try connecting using IP
            r = requests.get(f'http://{server_address}:{port}/{url}', timeout = timeout)
            return True, r
        except:
            # Server IP maybe already changed. Try to find the new IP using server_name           
            for i in range(3):
                if not self.stop_flag:
                    try:
                        # Try to get new IP
                        newIP = socket.gethostbyname(server_address)
                        # Try again using new IP
                        r = requests.get(f'http://{newIP}:{port}/{url}', timeout = timeout)
                        # Save new IP to file
                        self.update_server_addr(newIP)
                        return True, r
                    except Exception as e:
                        print (f'{e}: Failed getting server ip. Retry {i+1}...')
                        time.sleep(3)
                        continue
                else:
                    break
            return False, None


    def populate_items_to_list(self, devices):
        '''Populate items to a list widget'''
        for device in devices:
            self.deviceList.deviceListLayout.add_widget(device)


    def start_server_checker(self):
        '''Start the server checker thread'''
        self.server_box.server_item.start_server_checker()


    def start_devices_checker(self):
        '''Start the device checker threads'''
        #try:
        for device in self.devices:
            if self.stop_flag:
                # Stop starting device if the view is interrupted
                break
            device.start_device_checker()
        #except:
        #    print ('Device to start the thread')


    def update_server_addr(self, server_ip = '', server_name = ''):
        '''Serialize server ip and server name to file'''
        server_address = [server_ip, server_name]
        try:
            with open(self.serverAddressFile, 'wb') as file:
                pickle.dump(server_address, file)
        except Exception as e:
            print (f'Saving server address failed: {e}')


    def store_connected_device(self, deviceJSON):
        '''Serialize connected devices address to file'''
        try:
            with open(self.lastConnDevFile, 'wb') as file:
                pickle.dump(deviceJSON, file)
        except Exception as e:
            print (f'Saving last connected device failed: {e}')


    def button_press_callback(self, widget):
        if widget == self.ids.device_delete_button:
            widget.source = "images/settingview/delete_device_down.png"


    def button_release_callback(self, widget):
        if widget == self.ids.device_delete_button:
            widget.source = "images/settingview/delete_device_normal.png"


    def popup_button_callback(self, popup):
        # Callback function for manager popup button
        if not self.isServerTimeout:
            popup.title = 'Cancelling...'
            self.stop_flag = True
        else:
            popup.dismiss()
            self.isServerTimeout = False


    def stop(self):
        print ('stoping')
        self.stop_flag = True
        # Stopping the server checker thread
        self.server_box.server_item.stop_server_checker()
        # Stopping device checker threads
        try:
            for device in self.devices:
                device.stop_checker()
        except:
            print ('Device to stop the thread from')


    def open_popup(self, requester):
        # Open popup
        if type(requester) == ServerItem:
            # Server setting popup
            self.popup_requester = requester
            self.server_setting_popup.title = 'Change Server...'
            ## Fill the popup with current server setting
            self.server_setting_popup.server_setting.fill(requester)
            self.server_setting_popup.open()
        elif type(requester) == DeviceItem:
            # Device setting popup
            self.popup_requester = requester
            self.device_setting_popup.title = 'Device Setting'
            ## Fill the popup with current device setting
            self.device_setting_popup.device_setting.fill(requester)
            self.device_setting_popup.open()
        elif type(requester) == DeviceListBox:
            # Device add popup
            self.popup_requester = requester
            self.device_add_popup.title = 'Add Device'
            ## Fill the popup with current device setting
            self.device_add_popup.device_add.refresh()
            self.device_add_popup.open()


class ServerSettingPopup(Popup):

    server_setting = ObjectProperty(None)

    def __init__(self, caller, **kwargs):
        super(ServerSettingPopup, self).__init__(**kwargs)
        self.server_setting = ServerSetting(caller=caller)
        self.add_widget(self.server_setting)


class DeviceSettingPopup(Popup):

    device_setting = ObjectProperty(None)

    def __init__(self, caller, **kwargs):
        super(DeviceSettingPopup, self).__init__(**kwargs)
        self.device_setting = DeviceSetting(caller=caller)
        self.add_widget(self.device_setting)


class DeviceAddPopup(Popup):

    device_add = ObjectProperty(None)

    def __init__(self, caller, **kwargs):
        super(DeviceAddPopup, self).__init__(**kwargs)
        self.device_add = DeviceAdd(caller=caller)
        self.add_widget(self.device_add)