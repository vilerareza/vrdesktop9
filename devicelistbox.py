from kivy.properties import ObjectProperty 
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from devicelist import DeviceList

Builder.load_file('devicelistbox.kv')

class DeviceListBox(BoxLayout):
    
    setting_view = ObjectProperty(None)
    deviceListLayout = ObjectProperty(None)
    serverBox = ObjectProperty(None)
    settingContentBox = ObjectProperty(None)
    btn_device_add = ObjectProperty(None)
    btnRefresh = ObjectProperty

    def button_press_callback(self, button):
        if button == self.btn_device_add:
            button.source = 'images/settingview/btn_add_icon_down.png'
        elif button == self.btnRefresh:
            button.source = 'images/settingview/btn_refresh_down.png'

    def button_release_callback(self, button):
        if button == self.btn_device_add:
            button.source = 'images/settingview/btn_add_icon.png'
            self.setting_view.open_popup(self)
        elif button == self.btnRefresh:
            button.source = 'images/settingview/btn_refresh.png'
            self.settingView.init_views()