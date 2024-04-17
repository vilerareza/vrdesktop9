from kivy.properties import ObjectProperty, BooleanProperty
from kivy.uix.stacklayout import StackLayout
from kivy.lang import Builder

class DeviceList (StackLayout):

    selectedDevice = ObjectProperty(None)
    isDeviceSelected = BooleanProperty(False)
    # Handle property to the serverBox layout
    serverBox = ObjectProperty(None)
    settingContentBox = ObjectProperty(None)


