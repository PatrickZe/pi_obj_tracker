import logging
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
import sys
import threading
import time

from picamera2 import Picamera2, Preview
from picamera2.previews.qt import *
from libcamera import Transform

from PyQt5.QtWidgets import QApplication
from obj_tracker_gui import GuiApp as Obj_Tracker_GUI
from obj_tracker_qt import MainGUI, GUI_Thread

def gui_main_fun():
    app = QApplication(sys.argv)
    gallery = MainGUI()
    gallery.show()
    sys.exit(app.exec_())

if __name__ == "__main__":

    #gui = Obj_Tracker_GUI()

    #while True:
    #    gui.update()
    app = QApplication(sys.argv)
    cam = Picamera2()
    #cam.configure(cam.create_video_configuration(main={"size": (640, 480)}))
    config = cam.create_preview_configuration(main={"size": (640, 480)},
                                             lores={"size": (320, 240), "format": "YUV420"}, 
                                             transform=Transform(vflip=1))
    cam.configure(config)
    #cam.start_preview(Preview.QT)

    qtcam = QGlPicamera2(cam, width=640, height=480, keep_ar=False)
    print("helosa")

 
    gallery = MainGUI(cam=qtcam)
    
    cam.start()

    gallery.show()

    app.exec_()

    #gui_main_fun()

    print("Hello wordl2")
    