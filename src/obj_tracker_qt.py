
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
import cv2
import time
import numpy as np

#Picamera2
from picamera2 import Picamera2, Preview, MappedArray
from picamera2.previews.qt import QGlPicamera2
from libcamera import Transform


class GUI_Thread(QThread):

    def run(self):
        app = QApplication(sys.argv)
        gallery = MainGUI()
        gallery.show()
        sys.exit(app.exec_())

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


class VideoThread(QThread):
    new_aktor_data_available = pyqtSignal(int)

    def __init__(self, tilt, rotation,  parent=None):
        QThread.__init__(self, parent=parent)
        #Vars
        self.pixel_delta_x = 0
        self.pixel_delta_y = 0

        #aktors:
        self.tilt_mechanic = tilt
        self.rotation_mechanic = rotation
        #Setup Opencv
    
        self.face_detector_cv = cv2.CascadeClassifier("/home/patrick/dep/opencv/haarcascade_frontalface_default.xml")
        self.faces = []
        self.colors = []
        self.persons = []
        #print(f"\nTESTVAR: {test}\n")
        #face_detector = cv2.CascadeClassifier("/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml")
        #cv2.startWindowThread()

        self.picam2 = Picamera2()
        #self.picam2.configure(self.picam2.create_preview_configuration(main={"size": (640, 480), "format": "YUV420"}, transform=Transform(vflip=1)))
        #self.picam2.start()
        config = self.picam2.create_preview_configuration(   main={"size": (640, 480)},
                                                        lores={"size": (320, 240), "format": "YUV420"}, 
                                                        transform=Transform(vflip=1))
        self.picam2.configure(config)

        (self.w0, self.h0) = self.picam2.stream_configuration("main")["size"]
        (self.w1, self.h1) = self.picam2.stream_configuration("lores")["size"]
        self.s1 = self.picam2.stream_configuration("lores")["stride"]

        self.qtcam = QGlPicamera2(self.picam2, width=640, height=480, keep_ar=True)

        self.mode = "Raw"

        self.picam2.start()




    def run(self):

        while True:

            if self.mode == "Raw":
                self.show_raw()

            elif self.mode == "OpenCV face":
                buffer = self.picam2.capture_buffer("lores")
                grey = buffer[:self.s1 * self.h1].reshape((self.h1, self.s1))
                self.faces = self.face_detector_cv.detectMultiScale(grey, 1.1, 3)
            
            elif self.mode == "OpenCV color":
                buffer = self.picam2.capture_array("lores")
                bgr = cv2.cvtColor(buffer, cv2.COLOR_YUV420p2BGR) 
                hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV) 
                self.colors = self.color_detector_cv(hsv)

            else:
                pass



    def get_cam(self):
        return self.qtcam

    def switch_mode(self, new_mode: str):
        if new_mode == "Raw":
            self.picam2.post_callback = self.empty_callback
            self.mode = new_mode
        elif new_mode == "OpenCV face":
            self.picam2.post_callback = self.draw_faces_cv
            self.mode = new_mode
        elif new_mode == "OpenCV color":
            self.picam2.post_callback = self.draw_color_cv
            self.mode = new_mode
        elif new_mode == "TFL person":
            pass
        else:
            logging.warn("Mode not recognized!")
        
    def empty_callback(self, request):
        pass

    def draw_color_cv(self, request):
        
        with MappedArray(request, "main") as m:
            for cont in self.colors:
                (x,y,w,h) = cont
                x = x*2
                y = y*2
                w = w*2
                h = h*2
                cv2.rectangle(m.array, (x, y), (x + w, y + h), (0, 255, 0, 0))
                if len(self.colors) == 1:
                    self.get_pixel_delta_from_mid(x+0.5*w, y+0.5*h)
                    self.new_aktor_data_available.emit(1)

    def color_detector_cv(self, hsv_image):
        
        # arrays to hold lower and upper range
        # Green redbull: [70, 100, 100] and [120, 255, 255]
        lower_range = np.array([35, 70, 70], dtype=np.uint8) 
        upper_range = np.array([85, 255, 255], dtype=np.uint8)

        # create first mask from image
        color_mask = cv2.inRange(hsv_image, lower_range, upper_range)

        #define kernel size, (7,7) works good for indoor, green redbull
        kernel = np.ones((7,7),np.uint8)

        # Remove noise from mask
        mask = cv2.morphologyEx(color_mask, cv2.MORPH_CLOSE, kernel)  #black noise
        mask = cv2.morphologyEx(color_mask, cv2.MORPH_OPEN, kernel)   #white noise
        
        #Remove mask ->Display use only
        #seg_image =  cv2.bitwise_and(img, img, mask=mask)

        #find contours
        contours = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]

        #save contour rectangle
        ret_list = []
        if len(contours)>0:
            area = max(contours, key=cv2.contourArea)
            (x,y,w,h) = cv2.boundingRect(area)
            ret_list.append([x,y,w,h])
    
        return ret_list

    def draw_faces_cv(self, request):
        #print(request)
        #print(f"Faces: {self.faces}")
        with MappedArray(request, "main") as m:
            #logging.info(self.faces)
            for f in self.faces:
                (x, y, w, h) = [c * n // d for c, n, d in zip(f, (self.w0, self.h0) * 2, (self.w1, self.h1) * 2)]
                cv2.rectangle(m.array, (x, y), (x + w, y + h), (0, 255, 0, 0))

                if len(self.faces) == 1: 
                    self.get_pixel_delta_from_mid(x+0.5*w, y+0.5*h)
                    self.new_aktor_data_available.emit(1)
                else:
                    logging.warn(f"{len(self.faces)} faces detected.")
                    break

            #No faces found, countering last known drift
            if self.faces == []:
                self.pixel_delta_x = 0
                self.pixel_delta_y = 0
                logging.warn("No face detected")
                self.new_aktor_data_available.emit(1)


    def get_pixel_delta_from_mid(self, pixel_x: int, pixel_y: int):
        #hardcoded values
        size_x = 640
        size_y = 480

        self.pixel_delta_x = pixel_x - 0.5*size_x
        self.pixel_delta_y = pixel_y - 0.5*size_y


    def translate_and_emit_image(self, image):
        #height, width, channel = image.shape
        #bytes_per_line = 3 * width
        #q_img = QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888)

        #print(f"H: {height}, W: {width}")
        
        #self.change_pixmap.emit(q_img)
        pass
          
    def show_raw(self):
        # Deprecated
        image = self.picam2.capture_array()
        
        self.translate_and_emit_image(image)
        

    def show_opencv_face(self):
        #OpenCV Face
        #start_time = time.time()
        image = self.picam2.capture_array()
        grey = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_detector_cv.detectMultiScale(grey, 1.1, 5)

        for (x, y, w, h) in faces:
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0))
        self.translate_and_emit_image(image)
        #height, width, channel = im.shape
        #bytes_per_line = 3 * width
        #q_img = QImage(im.data, width, height, bytes_per_line, QImage.Format_RGB888)
        #print(f"H: {height}, W: {width}")
        #self.change_pixmap.emit(q_img)



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
        elif id == 2:
            self.algo_mode = "OpenCV color"
        elif id == 3:
            self.algo_mode = "OpenCV face"
        elif id == 4:
            self.algo_mode = "TFL person"
        else:
            pass

        logging.info(f"Now now showing picture in {self.algo_mode} mode.")
        self.video_thread.switch_mode(self.algo_mode)




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
