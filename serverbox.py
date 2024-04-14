from kivy.lang import Builder
from kivy.properties import BooleanProperty, ObjectProperty
from kivy.uix.floatlayout import FloatLayout

from serveritem import ServerItem

Builder.load_file("serverbox.kv")

class ServerBox(FloatLayout):

    server_item = ObjectProperty(None)
    titleLabel = ObjectProperty(None)

    deviceListLayout = ObjectProperty(None)
    settingContentBox = ObjectProperty(None)
    setting_view = ObjectProperty(None)
    serverItemSelected = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)