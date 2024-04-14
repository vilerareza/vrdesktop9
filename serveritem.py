from threading import Thread
import time
import requests
import socket
import pickle

from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
from mylayoutwidgets import ImageButton

Builder.load_file("serveritem.kv")


class ServerItem(FloatLayout):
    
    str_title = StringProperty('Server: ___.___.___.___')
    str_status = StringProperty('Disconnected')
    
    setting_view = ObjectProperty(None)
    lbl_address = ObjectProperty(None)
    img_server = ObjectProperty(None)
    img_status = ObjectProperty(None)
    btn_server_change = ObjectProperty(None)
    
    file_server_address = ''
    server_address = ''
    port = 8000
    t_check = 5
    stop_flag = False


    def __init__(self, server_address_file='data/serveraddress.p', **kwargs):
        super().__init__(**kwargs)
        try:
            self.file_server_address = server_address_file
            # Deserialize the server address
            with open(self.file_server_address, 'rb') as file:
                self.server_address = pickle.load(file)
                self.str_title = f'Server: [b]{self.server_address}[/b]'
        except Exception as e:
            print(f'{e}: Failed loading server address: {e}')


    def update_server_addr(self, server_address = ''):

        # Serialize server address to file
        try:
            with open(self.file_server_address, 'wb') as file:
                pickle.dump(self.server_address, file)

            # Updating the properties
            self.server_address = server_address
            self.str_title = f'Server: [b]{self.server_address}[/b]'
        
        except Exception as e:
            print (f'Saving server address failed: {e}')
        

    def send_request(self, server_address, server_port, url, timeout = 3):
        try:
            # Try connecting using IP
            r = requests.get(f'http://{server_address}:{server_port}/{url}', timeout = timeout)
            return True, r
        except:
            # Server IP maybe already changed. Try to find the new IP using server_name           
            for i in range(3):
                try:
                    if self.stop_flag:
                        break
                    # Try to get new IP
                    new_ip = socket.gethostbyname(server_address)
                    # Try again using new IP
                    r = requests.get(f'http://{new_ip}:{server_port}/{url}', timeout = timeout)
                    # Save new IP to file
                    self.update_server_addr(new_ip)
                    return True, r
                except Exception as e:
                    print (f'{e}: Failed getting server ip. Retry {i+1}...')
                    time.sleep(3)
                    continue
            return False, None  


    def start_server_checker(self):

        # Start the status checker thread
        self.stop_flag=False

        def callback_ok(*args):
            self.img_server.source = 'images/settingview/server_item_active.png'
            self.img_status.source = 'images/settingview/connected.png'
            self.str_status = 'Connected'
        
        def callback_fail(*args):
            self.img_server.source = 'images/settingview/server_item.png'
            self.img_status.source = 'images/settingview/disconnected.png'
            self.str_status = 'Disconnected'

        def check():
            while (not self.stop_flag):
                # Loop check, if the application exit then break the loop
                isSuccess, r = self.send_request(self.server_address, 8000, 'servercheck/', 5)
                if isSuccess:
                    # Connection ok
                    if r.status_code == 200 and r.text == 'ServerOk!':
                        Clock.schedule_once(callback_ok, 0)
                    else:
                        Clock.schedule_once(callback_fail, 0)
                else:
                    # Connection failed
                    Clock.schedule_once(callback_fail, 0)
                # Delay between check
                time.sleep(self.t_check)

        # Starting the server checker thread
        t = Thread(target = check)
        t.daemon = True
        t.start()


    def button_press_callback(self, button):
        if button == self.btn_server_change:
            button.source = 'images/settingview/btn_chg_server_down.png'

    def button_release_callback(self, button):
        if button == self.btn_server_change:
            button.source = 'images/settingview/btn_chg_server.png'
            self.setting_view.open_popup(self)

    def stop_server_checker(self):
        self.stop_flag=True



