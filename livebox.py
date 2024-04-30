import io
import os
import gc
import time
from datetime import datetime
from functools import partial
from threading import Thread, Condition

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.floatlayout import FloatLayout
from kivymd.uix.behaviors.hover_behavior import HoverBehavior
from kivymd.uix.floatlayout import MDFloatLayout
from kivy.graphics.texture import Texture
from kivy.core.image import Image as CoreImage

from tkinter import Tk, filedialog

from mylayoutwidgets import ColorFloatLayout

from livestream import LiveStream

import numpy as np


Builder.load_file('livebox.kv')


class LiveBox(MDFloatLayout, HoverBehavior):

    manager = ObjectProperty(None)
    closeMe = ObjectProperty(None)
    live_stream = ObjectProperty(None)
    liveActionBar = ObjectProperty(None)
    status = StringProperty("stop")
    moveEvent = None
    # Websockets
    wst = None
    wst_control = None
    # Stream monitor
    streamMon = None
    # Movement
    controlsEnabled = True
    moveRepetitionSec = 0.3
    moveDistance = 10
    # servo parameter
    servo_center_pos = 7
    servo_max_move = 1.7
    # Audio object
    audioReceiver = None
    audioTransmitter = None
    # Stop flag
    stop_flag = False


    def __init__(self, device, **kwargs):
        super().__init__(**kwargs)
        self.device = device
        self.condition = Condition()
        

    def on_enter(self, *args):
        self.show_controls()


    def on_leave(self, *args):
        self.hide_controls()


    def on_frame_(self, img_array):

        # Update the livestream texture with new frame
        def __update_frame(buff, *largs):
            data = buff.flatten()
            self.live_stream.texture.blit_buffer(data, bufferfmt="ubyte", colorfmt="rgb")
            self.live_stream.canvas.ask_update()

        Clock.schedule_once(partial(__update_frame, img_array), 0)


    def show_live_stream (self):
        # Start the live stream (Image object)
        try:
            # Re-init the texture of the liveStream object
            self.live_stream.texture = Texture.create()
            self.status = "play"
        except Exception as e:
            print (f'{e}: Failed starting websocket connection')


    def stop_live_stream (self):
        try:  
            # Reset the live action bar button state
            self.liveActionBar.reset()
            if self.streamMon:
                with self.condition:
                    self.condition.notify_all()
                    self.streamMon.join()
            # Change status
            self.status = "stop"
        except Exception as e:
            print ("Error to stop live stream...")
            print (e)
            self.status = "stop"


    def adjust_self_size(self, size):
        self.size = size
        self.adjust_livestream_size(size)


    def adjust_livestream_size(self, size):
        factor1 = size[0] / self.live_stream.width
        factor2 = size[1] / self.live_stream.height
        factor = min(factor1, factor2)
        target_size = ((self.live_stream.width * factor), (self.live_stream.height * factor))
        self.live_stream.size = target_size     


    def capture_image(self, file_name = ''):
        if file_name =='':
            self.live_stream.texture.save("test.png", flipped = False)


    def show_controls(self):
        self.liveActionBar.opacity  = 0.7
        self.closeMe.opacity = 0.7

    def hide_controls(self):
        self.liveActionBar.opacity  = 0
        self.closeMe.opacity = 0

    def reduce_action_control(self):
        # Disable some controls (audio and download) on live action bar
        self.liveActionBar.reduce_action_control()
    
    def restore_action_control(self):
        # Re-enable some controls (audio and download) on live action bar
        self.liveActionBar.restore_action_control()


    def button_touch_down(self, *args):

        # Movements
        if self.controlsEnabled:

            if args[0].collide_point(*args[1].pos):

                if args[0] == self.closeMe:
                    # Close button pressed. Change button appearance
                    args[0].source = 'images/multiview/close_down.png'


    def button_touch_up(self, *args):

        # Movements
        if self.controlsEnabled:

            if args[0].collide_point(*args[1].pos):

                if args[0] == self.closeMe:
                    # Close button pressed. Change button appearance
                    args[0].source = 'images/multiview/close_normal.png'
                    self.manager.mainTabs.multiView.remove_live_box(liveBox = self)
                    return

 
    def disable_controls(self):
        self.controlsEnabled = False
        self.liveActionBar.disabled = True
        

    def enable_controls(self):
        self.controlsEnabled = True
        self.liveActionBar.disabled = False