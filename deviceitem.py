import random
from kivy.lang import Builder
from kivy.graphics import Color, Rectangle
from kivy.properties import NumericProperty, ObjectProperty, StringProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label

from mylayoutwidgets import ColorLabel

Builder.load_file("deviceitem.kv")

class DeviceItem(FloatLayout):
    device_id = NumericProperty(0)
    name = StringProperty("")
    stream_url = ''
    desc = ''
    enabled = BooleanProperty(True)
    image = ObjectProperty(None)
    label = ObjectProperty(None)
    color = ObjectProperty((0,0,0))
    
    imagePath = "images/not_device_selected5.png"

    def __init__(self, 
                 device_id, 
                 name, 
                 stream_url, 
                 desc, 
                 enabled, 
                 **kwargs):
        
        super().__init__(**kwargs)
        self.padding = [10]
        self.spacing = 10
        self.device_id = device_id
        self.name = name
        self.stream_url = stream_url
        self.desc = desc
        self.enabled = enabled
