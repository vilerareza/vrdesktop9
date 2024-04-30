import pickle
import socket
import time
from functools import partial
from threading import Thread

import requests
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import ListProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from winerror import SPAPI_E_DEVICE_INTERFACE_REMOVED

from device import Device
from deviceicon import DeviceIcon
from livebox import LiveBox
from livegridlayout import LiveGridLayout

Builder.load_file("multiview.kv")


class MultiView(BoxLayout):

    # Grid layout for live stream
    live_grid = ObjectProperty(None)
    # Layout for device selection to stream
    selectionBox = ObjectProperty(None)
    # Selection scroll view
    selectionScroll = ObjectProperty(None)
    # List for live stream objects
    live_boxes = ListProperty([])
    # List for device selection icons
    device_icons = ListProperty([])
    # Application manager class
    manager = ObjectProperty(None)
    # Device icon selection scroll buttons
    selectionNextButton = ObjectProperty(None)
    selectionBackButton = ObjectProperty(None)
    selectionInterval = 4
    # Server
    serverAddress = []
    # Devices
    devices = []
    # Last connected device
    lastConnDevFile = 'data/lastconnecteddev.p'
    isServerTimeout = False
    stop_flag = False


    def __init__(self, server_address_file='data/serveraddress.p', **kwargs):
        super().__init__(**kwargs)
        # Getting the server adrress, deserialize the serveraddress.p
        self.serverAddressFile = server_address_file
        #self.liveGrid.bind(size = self.adjust_livebox_size)


    def init_views(self, *args):
        '''Initialize the view of this class'''
        self.init_devices()
            
    
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
        '''Retrieve devices from server REST API'''

        def _send_request():
            '''Thread function'''
            # Resetting the stop flag
            self.stop_flag = False
            # Send request to the server
            isSuccess, r = self.send_request(server_address, 8000, 'api/device/', 5)
            # Sending request complete. Run callback function
            Clock.schedule_once(partial(callback, isSuccess, r), 0)

        def callback(is_success, r, *args):
            
            '''Thread callback function'''  
            if is_success:
                devices_json = r.json()  # Produce list of dict
                
                # Dismissing popup message
                self.manager.popup.dismiss()
                
                if len(devices_json) > 0:

                    # Create device objects
                    devices = self.create_devices(devices_json)

                    # Create device icon and livebox object
                    self.create_deviceicon_livebox(devices)

                    # Initiate device stream in new thread
                    t_device_check = Thread(target = self.start_devices_stream)
                    t_device_check.daemon = True
                    t_device_check.start()

                    ## Showing initLabel
                    self.live_grid.show_initlabel() 

            else:
                if self.stop_flag:
                    # Triggered by cancellation                    
                    self.isServerTimeout = True
                    self.manager.popup.title = 'Cancelled. Use last connected device...'
                    self.manager.popup.button.text = 'OK'
                    # Clearing stop flag
                    self.stop_flag = False
                else:
                    # Timeout. Prompting user to acknowledge
                    self.isServerTimeout = True
                    self.manager.popup.title = 'Timeout. Use last connected device...'
                    self.manager.popup.button.text = 'OK'
                    print ('Get devices timeout')

        # Clearing previous device stream objects and icons if any
        if len(self.device_icons) > 0:
            self.stop_streams()
            self.stop_icons()

        # Starting the new thread
        t = Thread(target = _send_request)
        t.daemon = True
        t.start()


    def create_devices(self, devices_json):
        # Create device objects based on 'get devices' response from database

        ## Create devices
        try:
            for device in devices_json:
                device_id = device ['id']
                device_name = device ['name']
                stream_url = device['stream_url']
                desc = device['desc']
                enabled = device['enabled']
                flip = device['flip']

                device = Device(
                    device_id = device_id,
                    name = device_name,
                    stream_url = stream_url,
                    desc = desc,
                    enabled = enabled,
                    flip = flip,
                    )
                self.devices.append(device)
        
        except Exception as e:
            print (f'multiview:create_devices {e}')

        return self.devices
    

    def create_deviceicon_livebox(self, devices):
        '''Create device icon and live box based on 'get devices' response from database'''

        # Create device icons
        try:
            for device_ in devices:
                
                # Fill device icon list
                device_icon = DeviceIcon(
                    device = device_,
                    size_hint = (None, None),
                    size = (dp(181), dp(45))
                    )

                # Binding the touch down event to a function
                device_icon.bind(on_touch_down=self.icon_touch_action)
                
                # Appending to a list
                self.device_icons.append(device_icon)

                # Fill live box object list
                self.live_boxes.append(LiveBox(
                    device = device_
                    )
                )

            # Add deviceIcon content to selection box
            for icon in self.device_icons:
                self.selectionBox.add_widget(icon)

        except Exception as e:
            print (f'multiview:create_device_icon_livebox: {e}')


    def start_devices_stream(self):
        '''Start the devices'''
        #try:
        for device in self.devices:
            if self.stop_flag:
                # Stop starting device if the view is interrupted
                break
            device.start_stream()
        #except:
        #    print ('Device to start the thread')


    def send_request(self, server_name, port, url, timeout = 3):
        '''Send request using server_ip, if it fails try again using server_name'''
        try:
            # Try connecting using IP
            r = requests.get(f'http://{server_name}:{port}/{url}', timeout = timeout)
            return True, r
        except:
            # Server IP maybe already changed. Try to find the new IP using server_name           
            for i in range(3):
                if not self.stop_flag:
                    try:
                        # Try to get new IP
                        newIP = socket.gethostbyname(server_name)
                        # Try again using new IP
                        r = requests.get(f'http://{newIP}:{port}/{url}', timeout = timeout)
                        # Save new IP to file
                        self.update_server_addr(newIP, server_name)
                        return True, r
                    except Exception as e:
                        print (f'{e}: Failed getting server ip. Retry {i+1}...')
                        time.sleep(3)
                        continue
                else:
                    break
            return False, None


    def update_server_addr(self, server_ip = '', server_name = ''):
        '''Serialize server ip and server name to file'''
        server_address = [server_ip, server_name]
        try:
            with open(self.serverAddressFile, 'wb') as file:
                pickle.dump(server_address, file)
        except Exception as e:
            print (f'Saving server address failed: {e}')


    def icon_touch_action(self, device_icon, touch):
        
        '''When user touch on device icon, show the respective live stream onject (livebox)'''
        if device_icon.collide_point(*touch.pos):
            
            # if not device_icon.disabled:

            #     if device_icon.is_connected:
            if self.live_boxes[self.device_icons.index(device_icon)].status != "play":
                # If the live stream object status is not playing then add #
                self.show_live_box(device_icon)
            else:
                # If the live stream object status is playing then remove
                self.remove_live_box(deviceIcon=device_icon)
                # else:
                #     # Try get the device IP again
                #     device_icon.get_device_ip()
            

    def show_live_box(self, device_icon):
        '''Show the live stream object based on selected device icon'''

        # Determine the corresponding live box based on device_icon index
        live_box_idx = self.device_icons.index(device_icon)
        # Remove the initLabel if there is no live_box is showing
        if self.live_grid.nLive == 0:
            self.live_grid.hide_initlabel()
        # Show the livebox
        self.live_boxes[live_box_idx].show_live_stream()   
        # Adjust live grid row and cols for displaying live stream #
        self.adjust_livegrid(action = 'add')
        # Display the live stream object to live grid layout
        self.live_grid.add_widget(self.live_boxes[live_box_idx])
        # Adjust the livestream to the size of livebox
        self.adjust_livebox_size()
        # Change the icon image to play
        device_icon.statusImage.source = 'images/multiview/play.png'


    def remove_live_box(self, deviceIcon=None, liveBox=None):

        if liveBox:
            '''Stop live stream object based on direct request from livebox'''
            liveBox.stop_live_stream()
            # Remove live stream object from live grid layout
            self.live_grid.remove_widget(liveBox)
            self.device_icons[self.live_boxes.index(liveBox)].statusImage.source = 'images/multiview/standby.png'
        else:
            '''Stop live stream object based on selected device icon'''
            self.live_boxes[self.device_icons.index(deviceIcon)].stop_live_stream()
            # Remove live stream object from live grid layout
            self.live_grid.remove_widget(self.live_boxes[self.device_icons.index(deviceIcon)])
            # Change the icon image to standby
            deviceIcon.statusImage.source = 'images/multiview/standby.png'

        # Re-adjust live grid rows and cols
        if self.adjust_livegrid(action = 'remove') > 0:
            # Adjust the livestream to the size of livebox
            self.adjust_livebox_size()
        else:
            # Showing initLabel
            self.live_grid.show_initlabel()
        #print (f'ROWS : {self.liveGrid.rows} COLS : {self.liveGrid.cols}')


    def adjust_livegrid(self, action = 'add'):
        '''Adjust liveGrid rows and collumns based on add / remove of livebox. Return True if success'''
        if action == 'add':
            self.live_grid.nLive +=1
            rowLimit = self.live_grid.rows**2 + self.live_grid.rows
            if self.live_grid.nLive > rowLimit:
                self.live_grid.rows +=1
            colLimit = self.live_grid.cols**2
            if (self.live_grid.nLive > colLimit):
                self.live_grid.cols +=1
        elif action == 'remove':
            self.live_grid.nLive -=1
            if self.live_grid.nLive > 0:
                rowLimit = (self.live_grid.rows-1)**2 + (self.live_grid.rows-1)
                if self.live_grid.nLive <= rowLimit:
                    self.live_grid.rows -=1
                colLimit = (self.live_grid.cols-1)**2
                if (self.live_grid.nLive <= colLimit):
                    self.live_grid.cols -=1
        # Return the number of livebox    
        return self.live_grid.nLive

    def adjust_livebox_size(self, *args):
        '''Adjust the size of individual livebox based on the row and col in the liveGrid'''
        cell_width = ((self.live_grid.width - self.live_grid.spacing[0]*(self.live_grid.cols-1))/
                    self.live_grid.cols)
        cell_height = ((self.live_grid.height - self.live_grid.spacing[0]*(self.live_grid.rows-1))/
                    self.live_grid.rows)
        for livebox in self.live_boxes:
            livebox.adjust_self_size(size = (cell_width, cell_height))
            # Disabled audio and download button on livebox if there is > 1 livebox
            if self.live_grid.nLive > 1:
                livebox.reduce_action_control()
            if self.live_grid.nLive == 1:
                livebox.restore_action_control()
        #print (f'GRID SIZE {self.liveGrid.size}, CELL SIZE {cell_width}, {cell_height}')

    def stop_icons(self):
        '''Trigger deviceIcon objects to stop running thread'''
        for deviceIcon in self.device_icons:
            deviceIcon.stop()
        self.selectionBox.clear_widgets()
        self.device_icons.clear()

    def stop_streams(self):
        '''Stop live streams anyway'''
        for liveBox in self.live_boxes:
            liveBox.stop_live_stream()
        # Reset and clearing widgets from liveGrid
        self.live_grid.clear_widgets()
        self.live_grid.nLive = 0
        self.live_grid.rows = 1
        self.live_grid.cols = 1
        # Clear the list of live stream objects
        self.live_boxes.clear()

    def stop(self):
        self.stop_flag = True
        self.stop_streams()
        self.stop_icons()
  
    def selection_next_press(self, button):
        if self.selectionScroll.scroll_x < 1:
            self.selectionScroll.scroll_x += 0.1
            if self.selectionScroll.scroll_x >= 1:
                self.selectionScroll.scroll_x = 1

    def selection_back_press(self, button):
        if self.selectionScroll.scroll_x > 0:
            self.selectionScroll.scroll_x -= 0.1
            if self.selectionScroll.scroll_x <= 0:
                self.selectionScroll.scroll_x = 0
    
    def popup_button_callback(self, popup):
        # Callback function for manager popup button
        if not self.isServerTimeout:
            popup.title = 'Cancelling...'
            self.stop_flag = True
        else:
            popup.dismiss()
            # Unable to get devices from server. Try getting the last connected device from file
            with open(self.lastConnDevFile, 'rb') as file:
                devices = pickle.load(file)
            if len(devices) > 0:
                pass
                # Create device icon and livebox object
                #if self.create_deviceicon_livebox(devices):
                #    self.start_icons()
                    # Showing initLabel
                #    self.liveGrid.show_initlabel()
            self.isServerTimeout = False
