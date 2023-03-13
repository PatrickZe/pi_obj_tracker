#############################################
# Raspberry Pi based Object Tracker
# DHBW Embedded Systems project
# Author: Patrick Zeitlmayr
#
# File: aktor_qt.py
#
#
#
#############################################

import time
from PyQt5.QtCore import QThread


class AktorThread(QThread):
    def __init__(self, tilt, rotation, parent=None) -> None:

        #Inherit from thread
        QThread.__init__(self, parent=parent)

        #Reference the software handlers
        self.tilt_mechanics = tilt
        self.rotation_mechanics = rotation

        #Vars
        self.tilt_pixels = 0    
        self.rotation_pixels = 0

        self.active = False #False == Manual, True == Automatic mode
        self.dt = 0.1 #timing delta for the PID-Controller


    def run(self):
        #Main loop, runs every dt seconds
        start_time = time.time()
        while True:
            if self.active == True:
                dtime = time.time() - start_time
                if dtime >= self.dt:
                    #min dt reached -> reposition the servos
                    self.tilt_mechanics.set_pixel_delta(self.tilt_pixels, dt=dtime) 
                    self.rotation_mechanics.set_pixel_delta(self.rotation_pixels, dt=dtime)

                    start_time = time.time()
