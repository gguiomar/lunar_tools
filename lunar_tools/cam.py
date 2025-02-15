# Copyright 2022 Lunar Ring. All rights reserved.
# Written by Johannes Stelzer, email stelzer@lunar-ring.ai twitter @j_stelzer

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import numpy as np
import cv2
import time
import sys
import time
import glob
import threading
import time
import glob
import os
from lunar_tools.utils import get_os_type


class WebCam():
    def __init__(self, cam_id=0, shape_hw=(576,1024)):
        """
        """
        self.do_mirror = False
        self.shift_colors = True
        self.cam_id = cam_id
        self.shape_hw = shape_hw
        self.img_last = np.zeros((shape_hw[0], shape_hw[1], 3), dtype=np.uint8)
        self.device_ptr = 0
        self.sleep_time_thread = 0.001 
        self.smart_init()
        
        self.threader_active = True
        self.thread = threading.Thread(target=self.threader_runfunc_cam, daemon=True)
        self.thread.start()
            
                
    def init_ubuntu(self):
        device_paths = glob.glob('/dev/video*')
        if len(device_paths) == 0:
            raise ValueError("No cameras found")
        if self.cam_id == -1:
            device_ptr = device_paths[0]
        else:
            device_ptr = f'/dev/video{self.cam_id}'
        self.cam = cv2.VideoCapture(device_ptr)
        
        while True:
            self.release()
            if self.cam_id == -1 and len(device_paths) > 1:
                device_paths.remove(device_ptr)
                device_ptr = device_paths[0]
                print(f"smart_init: using device_ptr {device_ptr}")
            
            self.cam = cv2.VideoCapture(device_ptr)
            self.set_cap_props()
            _, img = self.cam.read()
            if img is not None:
                break
            print("release loop...")
            time.sleep(0.2)
        self.device_ptr = device_ptr
        
    def init_mac(self):
        self.cam = cv2.VideoCapture(self.cam_id, cv2.CAP_AVFOUNDATION)
        
    def release(self):
        self.threader_active = False
        self.thread.join()
        self.cam.release()
        cv2.destroyAllWindows()
        cv2.VideoCapture(self.cam_id).release()    

    def smart_init(self):
        if get_os_type() == "Ubuntu":
            self.init_ubuntu()
        elif get_os_type() == "MacOS":
            self.init_mac()
        else:
            raise NotImplementedError("Only Ubuntu and Mac supported.")
        self.set_cap_props()
        
    def set_cap_props(self):
        codec = 0x47504A4D  # MJPG
        self.cam.set(cv2.CAP_PROP_FPS, 30.0)
        self.cam.set(cv2.CAP_PROP_FOURCC, codec)
        self.cam.set(cv2.CAP_PROP_FRAME_WIDTH,self.shape_hw[1])
        self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT,self.shape_hw[0])

    def set_focus_inf(self):
        self.cam.set(cv2.CAP_PROP_AUTOFOCUS, 0)
        self.cam.set(cv2.CAP_PROP_FOCUS, 0)
        
    def set_autofocus(self):
        self.cam.set(cv2.CAP_PROP_AUTOFOCUS, 1)

    def threader_runfunc_cam(self):
        while self.threader_active:
            img = self.get_raw_image()
            if img is None:
                print("threader_runfunc_cam: bad img is None. trying to repair...")
                self.cam.release()
                cv2.VideoCapture(self.device_ptr).release()
                self.smart_init()
                time.sleep(1)
            else:
                self.img_last = self.process_raw_image(img)
            time.sleep(self.sleep_time_thread)

    def get_raw_image(self):
        _, img = self.cam.read()
        if img is None or img.size < 100:
            print("get_raw_image: fail, image is bad.")
            return
        return img

    def process_raw_image(self, img):
        if self.shift_colors:
            img = np.flip(img, axis=2)
        if self.do_mirror:
            img = np.flip(img, 1)
        return img
    
    def get_img(self):
        return self.img_last

        
if __name__ == "__main__":
    from PIL import Image
    cam = WebCam()
    img = cam.get_img()
    img = Image.fromarray(img)
    img.show()
    

    
    