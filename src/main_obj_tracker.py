#!/usr/bin/env python

#############################################
# Raspberry Pi based Object Tracker
# DHBW Embedded Systems project
# Author: Patrick Zeitlmayr
#
# File: Main entry point
#
# Setup:
#   - sudo pigpiod (Pigpio deamon)
#
#
#############################################

import logging
logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=logging.INFO)
import sys


from PyQt5.QtWidgets import QApplication
#from obj_tracker_gui import GuiApp as Obj_Tracker_GUI
from obj_tracker_qt import MainGUI

from servos_pid import Tracker_Servos


if __name__ == "__main__":

    ###
    # Setup of the 2 Servos
    ###
    rotation_mechanic = Tracker_Servos(18)
    rotation_mechanic.set_dc_boundary(2.5, 12.5)

    tilt_mechanic = Tracker_Servos(13)
    tilt_mechanic.set_dc_boundary(2.5, 10)

    ###
    # Starting the Qt Application
    ###
    app = QApplication(sys.argv)
    gallery = MainGUI(tilt_mechanic, rotation_mechanic)
    gallery.show()

    sys.exit(app.exec_())


    
    