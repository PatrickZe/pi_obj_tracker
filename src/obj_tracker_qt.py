
#!/usr/bin/env python

#############################################
# Raspberry Pi based Object Tracker
# DHBW Embedded Systems project
# Author: Patrick Zeitlmayr
#
# File: Qt application 
#

#
#
#############################################

#QT
from PyQt5.QtCore import *#QDateTime, Qt, QTimer, pyqtSlot
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *#(QApplication, QImage,
        #QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QRadioButton, QVBoxLayout, QWidget, QButtonGroup)

#MISC
import sys
import logging
import time
import numpy as np
from pathlib import Path

#Own
from aktor_qt import AktorThread
from video_qt import VideoThread



class MainGUI(QDialog):
    def __init__(self, tilt_mechanic, rotation_mechanic, parent=None):
        super(MainGUI, self).__init__(parent)

        #VARS
        self.controll_mode = "Manual" #Manual or Automatic
        self.algo_mode = "Raw"  #Used algorithm for tracking, raw == none

 

        #self.originalPalette = QApplication.palette()

        self.image = QPixmap()
        self.image_label = QLabel()

        #Video
        self.video_thread = VideoThread(rotation_mechanic, tilt_mechanic, self)
        #setup video widget
        self.qtcam = self.video_thread.get_cam()
        self.video_thread.new_aktor_data_available.connect(self.aut_aktor_change)
        self.video_thread.start()

        #Aktors
        #Reference
        self.tilt_mechanic = tilt_mechanic
        self.rotation_mechanic = rotation_mechanic
        #start new thread
        self.aktor_thread = AktorThread(tilt_mechanic, rotation_mechanic, self)
        self.aktor_thread.start()


        ########
        # QT Application Setup
        ########
        #Groupboxes
        self.create_man_auto_group_box()
        self.create_algorithm_group_box()
        self.create_manual_sliders()

        #Toplayout
        topLayout = QHBoxLayout()
        topLayout.addStretch(1)

        #add Widget to toplayout in grid style
        mainLayout = QGridLayout()
        mainLayout.addLayout(topLayout, 0, 0, 1, 2)
        mainLayout.addWidget(self.man_auto_group_box, 1, 0)
        mainLayout.addWidget(self.algorithm_group_box, 0, 0 )
        mainLayout.addWidget(self.manual_sliders, 1, 1)

        #Fixed height/width for video
        self.qtcam.setFixedWidth(640)
        self.qtcam.setFixedHeight(480)
        mainLayout.addWidget(self.qtcam, 0,1)

        #Optical finetuning
        mainLayout.setRowStretch(1, 1)
        mainLayout.setRowStretch(2, 1)
        mainLayout.setColumnStretch(0, 1)
        mainLayout.setColumnStretch(1, 1)

        #Finalizing
        self.setLayout(mainLayout)
        self.setWindowTitle("Object Tracker - Embedded Systems Project")

    def create_man_auto_group_box(self):
        # Creates a group box with Radio buttons to switch Manual/Automatic - Mode

        # Setup Group with 2 Radio button
        self.man_auto_group_box = QGroupBox("Controll Mode")
        self.radio_auto = QRadioButton("Automatic")
        self.radio_manual = QRadioButton("Manual")

        # Default: Manual mode
        self.radio_manual.setChecked(True)

        # Enclose in a Button Group for easier event-handling
        self.man_auto_button_group = QButtonGroup()
        self.man_auto_button_group.addButton(self.radio_auto, 2)
        self.man_auto_button_group.addButton(self.radio_manual, 1)

        # Signal connections
        self.man_auto_button_group.buttonClicked.connect(self.change_man_auto_mode)

        # finalize Layout
        layout = QVBoxLayout()
        layout.addWidget(self.radio_manual)
        layout.addWidget(self.radio_auto)
        layout.addStretch(1)
        self.man_auto_group_box.setLayout(layout)


    def create_algorithm_group_box(self):
        # Creates a group box with Radio Buttons to switch the used Algorithms

        # Setup Group with the options
        self.algorithm_group_box = QGroupBox("Tracking Algorithm")
        raw = QRadioButton("Raw Image")
        opencv_color = QRadioButton("OpenCV color")
        opencv_face = QRadioButton("OpenCV face")
        tensorflow_person = QRadioButton("Tensorflow person")

        # Default: Raw image
        raw.setChecked(True)

        # Enclose in a button group for easier event handling
        self.algorithm_button_group = QButtonGroup()
        self.algorithm_button_group.addButton(raw, 1)
        self.algorithm_button_group.addButton(opencv_color, 2)
        self.algorithm_button_group.addButton(opencv_face, 3)
        self.algorithm_button_group.addButton(tensorflow_person, 4)

        # Signal connections
        self.algorithm_button_group.buttonClicked.connect(self.change_algorithm)

        # Finalize Layout
        layout = QVBoxLayout()
        layout.addWidget(raw)
        layout.addWidget(opencv_color)
        layout.addWidget(opencv_face)
        layout.addWidget(tensorflow_person)

        layout.addStretch(1)
        self.algorithm_group_box.setLayout(layout)



    def create_manual_sliders(self):
        # Creates a group box for the manual controll sliders


        self.manual_sliders = QGroupBox("Manual controll Sliders")
        self.manual_sliders.setEnabled(True)

        # Slider 1: Rotation Setup
        slider_rotation = QSlider(Qt.Orientation.Horizontal, self.manual_sliders)
        slider_rotation.setMinimum(-90)
        slider_rotation.setMaximum(90)
        slider_rotation.setSingleStep(1)
        slider_rotation.setValue(0)
        

        # Slider 2: Tilt Setup
        slider_tilt = QSlider(Qt.Orientation.Horizontal, self.manual_sliders)
        slider_tilt.setMinimum(-50)  #Negaitve Tilt limited by construction
        slider_tilt.setMaximum(90)
        slider_tilt.setSingleStep(1)
        slider_tilt.setValue(0)

        # Labels
        self.label_rotation = QLabel(self.manual_sliders)
        self.slider_rot_change(0)

        self.label_tilt = QLabel(self.manual_sliders)
        self.slider_tilt_change(0)


        # connections
        slider_rotation.valueChanged.connect(self.slider_rot_change)
        slider_tilt.valueChanged.connect(self.slider_tilt_change)

        # Finalize Layout
        layout = QGridLayout()
        layout.addWidget(self.label_rotation, 0,0)
        layout.addWidget(slider_rotation, 3, 0)
        layout.addWidget(self.label_tilt, 4, 0)
        layout.addWidget(slider_tilt, 5, 0)
        layout.setRowStretch(5, 1)
        self.manual_sliders.setLayout(layout)
    
    def slider_rot_change(self, value):
        # Changes rotation label&Servo when the slider is moved
        self.label_rotation.setText(f"Rotation:\t{value}°")
        self.rotation_mechanic.set_angle(float(value))

    def slider_tilt_change(self, value):
        # Changes tilt label&Servo when the slider is moved
        self.label_tilt.setText(f"Tilt: \t\t{value}°")
        self.tilt_mechanic.set_angle(float(-1*value))

    def aut_aktor_change(self):
        # Changes the servos in automatic mode
        if self.controll_mode == "Automatic":
            self.aktor_thread.tilt_pixels = self.video_thread.pixel_delta_y
            self.aktor_thread.rotation_pixels = self.video_thread.pixel_delta_x 
        else:
            return 

        

    def change_man_auto_mode(self, object):
        # Callback for Man/auto button group
        # Handles the mode-selection

        #Get the button id, 1=Manual, 2 = Auto
        id = self.man_auto_button_group.id(object) 
        
        if id == 1:
            #New Mode: Manual
            self.controll_mode = "Manual"
            self.manual_sliders.setEnabled(True)
            self.aktor_thread.active = False
        else:
            # New Mode: Automatic
            self.controll_mode = "Automatic"
            self.manual_sliders.setEnabled(False)
            self.aktor_thread.active = True

        logging.info(f"Now in {self.controll_mode} mode.")

    def change_algorithm(self, object):
        #Callback for algo button group
        # Handles Algorithm selection

        # Get the button id, 1=Raw, 2=CV color, 3= cv face, 4=tfl
        id = self.algorithm_button_group.id(object) 
        if id == 1:
            self.algo_mode = "Raw"
            speed = "fast"
        elif id == 2:
            self.algo_mode = "OpenCV color"
            speed = "fast"
        elif id == 3:
            self.algo_mode = "OpenCV face"
            speed = "fast"
        elif id == 4:
            self.algo_mode = "TFL person"
            speed = "slow"
        else:
            pass

        logging.info(f"Now now showing picture in {self.algo_mode} mode.")
        self.video_thread.switch_mode(self.algo_mode)

        #Switch pid-speed, tensorflow is really slow 
        if speed == "fast":
            self.aktor_thread.dt = 0.1
        else:
            self.aktor_thread.dt = 0.5




#########################
# For testing without seperate main-file
#########################


#if __name__ == '__main__':
#
#    import sys
#
#    app = QApplication(sys.argv)
#    gallery = MainGUI()
#    gallery.show()
#    sys.exit(app.exec_())
