from threading import Thread
import time
import requests
import socket

from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
from mylayoutwidgets import ImageButton

Builder.load_file("serversetting.kv")


class ServerSetting(FloatLayout):

    server_obj = None
    titleLabel = ObjectProperty(None)
    server_address_label = ObjectProperty(None)
    server_address_text = ObjectProperty(None)
    btn_save = ObjectProperty(None)
    btn_cancel = ObjectProperty(None)
    btn_test = ObjectProperty(None)
    lbl_test = ObjectProperty(None)
    img_test = ObjectProperty(None)
    str_lbl_test = StringProperty('')

    serverAddressFile = 'data/serveraddress.p'


    def __init__(self, caller=None, **kwargs):
        super(ServerSetting, self).__init__(**kwargs)
        self.caller = caller


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
        self.lbl_test.text = ''
        self.img_test.opacity = 0            
    
    
    def fill(self, server_item):
        # Reset the widgets state
        self.reset()
        # Fill the widgets with current setting. The server_obj is the ServerItem object
        if server_item:
            # Getting the server object
            self.server_obj = server_item
            # Updating the text with serverObj server address property
            self.server_address_text.text = str(server_item.server_address)


    def test_server(self, server_ip, port = 8000):
        '''Start the server status checker thread'''

        def callback_ok(*args):
            self.str_lbl_test = 'Server OK'
            self.img_test.opacity = 1
            self.img_test.source = 'images/settingview/server_ok.png'
        
        def callback_fail(*args):
            self.str_lbl_test = 'Server Not Found'
            self.img_test.opacity = 1
            self.img_test.source = 'images/settingview/server_fail.png'

        def check():
            try:
                print ('start', server_ip)
                r = requests.get(f'http://{server_ip}:{port}/servercheck/', timeout = 5)
                if r.status_code == 200 and r.text == 'ServerOk!':
                    Clock.schedule_once(callback_ok, 0)
                    print ('OK')
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
        elif button == self.btn_test:
            button.source =  'images/settingview/btn_test_down.png'


    def button_release_callback(self, button):

        if button == self.btn_save:
            button.source = 'images/settingview/btn_save_server.png'
            server_address = self.save_server_addr(self.server_address_text)
            # Dismissing popup
            if server_address != '':
                self.caller.server_setting_popup.dismiss()
            
        elif button == self.btn_cancel:
            button.source =  'images/settingview/btn_cancel.png'
            # Dismissing popup
            self.caller.server_setting_popup.dismiss()
            
        elif button == self.btn_test:
            button.source =  'images/settingview/btn_test.png'
            # Validates entry and perform connection test to server
            if self.validate_entry(self.server_address_text):
                self.str_lbl_test = 'Testing...'
                self.img_test.opacity = 0
                self.test_server(self.server_address_text.text)


