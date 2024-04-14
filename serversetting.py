from threading import Thread
import time
import requests
import socket

from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from mylayoutwidgets import ImageButton

Builder.load_file("serversetting.kv")


class ServerSetting(FloatLayout):

    server_obj = None
    titleLabel = ObjectProperty(None)
    server_address_label = ObjectProperty(None)
    server_address_text = ObjectProperty(None)
    myParent = ObjectProperty(None)
    btn_save = ObjectProperty(None)
    btn_cancel = ObjectProperty(None)

    serverAddressFile = 'data/serveraddress.p'


    def __init__(self, caller=None, **kwargs):
        super(ServerSetting, self).__init__(**kwargs)
        self.caller = caller

    # def toggle_press_callback(self, button):
    #     '''callback function for edit/save button'''
    #     if button == self.btnSaveEdit:
    #         if button.state == 'down':
    #             self.editMode = True
    #         else:
    #             self.editMode = False
    #             if not self.isReset:
    #                 # Only save the server address when toggle is not triggered by reset method
    #                 # Serializing server IP and server name
    #                 print ('save server address')
    #                 serverIP, serverName = self.save_server_addr(self.serverAddressText)
    #                 if serverIP:
    #                     # Test the connection to the server in different thread
    #                     self.test_server(serverIP)
    #                     # Refresh the devices
    #                     #self.parent.reinit_views()


    def save_server_addr(self, entry_widget):
        '''Updating the server IP and server host name'''
        server_address = ''
        try:
            if self.validate_entry(entry_widget):
                # If entry is not empty then process
                server_address = entry_widget.text
                if self.server_obj:
                    # server_obj is serveritem
                    self.server_obj.update_server_addr(server_address)
        finally:
            return server_address


    def validate_entry(self, *args):
        # Validate if user input is not empty
        is_valid = True
        for entry in args:
            if entry.text == '':
                is_valid = False
                entry.background_color = (0.9, 0.7, 0.7)
            else:
                entry.background_color = (1, 1, 1)
        return is_valid


    def get_server_ip(self, server_name):
        # Get server ip address from entered server hostname
        serverIP = ''      
        for i in range(3):
            # Perform 3 times trial
            try:
                serverIP = socket.gethostbyname(server_name)
                break
            except Exception as e:
                print (f'{e}: Failed getting server ip. Retry {i+1}...')
                time.sleep(3)
                continue        
        return serverIP
    

    def reset(self):
        # Reset the widgets state
        self.server_address_text.background_color = (1, 1, 1)
        # self.testLabel.text = ''
        # self.testImage.opacity = 0            
    
    
    def fill(self, server_item):
        # Reset the widgets state
        self.reset()
        # Fill the widgets with current setting. The server_obj is the ServerItem object
        if server_item:
            # Getting the server object
            self.server_obj = server_item
            # Updating the text with serverObj server address property
            self.server_address_text.text = server_item.server_address


    def test_server(self, server_ip, port = 8000):
        '''Start the server status checker thread'''

        def callback_ok(*args):
            self.testLabel.text = 'Server OK'
            self.testImage.opacity = 1
            self.testImage.source = 'images/settingview/server_ok.png'
        
        def callback_fail(*args):
            self.testLabel.text = 'Server Not Found'
            self.testImage.opacity = 1
            self.testImage.source = 'images/settingview/server_fail.png'

        def check():
            try:
                r = requests.get(f'http://{server_ip}:{port}/servercheck/', timeout = 5)
                if r.status_code == 200 and r.text == 'ServerOk!':
                    Clock.schedule_once(callback_ok, 0)
                else:
                    Clock.schedule_once(callback_fail, 0)
            except Exception as e:
                Clock.schedule_once(callback_fail, 0)
                print (f'test_server failed :{e}')

        t = Thread(target = check)
        t.daemon = True
        t.start()


    def button_press_callback(self, button):
        if button == self.btn_save:
            button.source =  'images/settingview/btn_save_server_down.png'
        elif button == self.btn_cancel:
            button.source =  'images/settingview/btn_cancel_down.png'


    def button_release_callback(self, button):

        if button == self.btn_save:
            server_address = self.save_server_addr(self.server_address_text)
            # Dismissing popup
            if server_address != '':
                self.caller.setting_popup.dismiss()
            button.source = 'images/settingview/btn_save_server.png'
        
        elif button == self.btn_cancel:
            # Dismissing popup
            self.caller.setting_popup.dismiss()
            button.source =  'images/settingview/btn_cancel.png'


