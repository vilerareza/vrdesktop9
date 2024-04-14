from kivy.graphics import Color, Rectangle
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

from serveritem import ServerItem
from deviceitem import DeviceItem
from serversetting import ServerSetting
from settingcontentcamera import SettingContentCamera
from settingaddcamera import SettingAddCamera

Builder.load_file("settingcontentbox.kv")

class SettingContentBox(BoxLayout):
    settingView = ObjectProperty(None)
    serverBox = ObjectProperty(None)
    deviceList = ObjectProperty(None)
    noSelectionLabel = ObjectProperty(None)
    #noSelectionText = 'Select Server or Camera for Setting...'
    settingContentServer = ServerSetting()
    settingContentCamera = SettingContentCamera()
    settingAddCamera = SettingAddCamera()

    def change_config(self, obj = None):
        '''Changing the child widget based on the obj selected'''
        self.clear_widgets()
        if type(obj) == DeviceItem:
            # Filling the settingContentDevice with object attribute
            self.settingContentCamera.populate(obj)
            # Adding the widget
            self.add_widget(self.settingContentCamera)
        elif obj == self.deviceList:
            self.add_widget(self.settingAddCamera)
        elif type(obj) == ServerItem:
            # Server setting. Show settingContentServer
            self.settingContentServer.fill(obj)
            self.add_widget(self.settingContentServer)

    def no_selection_config(self):
        # Clearing widgets
        self.clear_widgets()
        self.add_widget(self.noSelectionLabel)

    def reinit_views(self):
        # Reinitializing devices
        self.settingView.init_views()

    def update_deviceitem(self, new_device):
        # Update the edited device. new_device_obj is the new data for edited device
        self.settingView.update_deviceitem(new_device)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.noSelectionLabel = NoSelectionLabel()

class NoSelectionLabel(Label):
    pass
    
