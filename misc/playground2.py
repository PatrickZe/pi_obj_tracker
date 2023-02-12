import cv2
import numpy as np
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QDialog, QLabel, QGridLayout
from picamera2 import Picamera2, Preview, MappedArray
from libcamera import Transform
#import picamera2.array
import time


class VideoThread(QThread):
    change_pixmap = pyqtSignal(QImage)

    def __init__(self, parent=None):
        QThread.__init__(self, parent=parent)
        #Setup Opencv
    
        self.face_detector_cv = cv2.CascadeClassifier("/home/patrick/dep/opencv/haarcascade_frontalface_default.xml")

        #print(f"\nTESTVAR: {test}\n")
        #face_detector = cv2.CascadeClassifier("/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml")
        #cv2.startWindowThread()

        self.picam2 = Picamera2()
        self.picam2.configure(self.picam2.create_preview_configuration(main={"size": (640, 480), "format": "BGR888"}, transform=Transform(vflip=1)))
        self.picam2.start()




    def run(self):

        while True:
            start_time = time.time()
            im = self.picam2.capture_array()

            grey = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
            faces = self.face_detector_cv.detectMultiScale(grey, 1.1, 5)
#
            for (x, y, w, h) in faces:
                cv2.rectangle(im, (x, y), (x + w, y + h), (0, 255, 0))

            height, width, channel = im.shape
            bytes_per_line = 3 * width
            q_img = QImage(im.data, width, height, bytes_per_line, QImage.Format_RGB888)
            #q_pix = QPixmap(w=width, h=height, )
            #p = q_img.scaled(640, 480, Qt.KeepAspectRatio)
            print(f"H: {height}, W: {width}")
            self.change_pixmap.emit(q_img)


            #time.sleep(0.05)
            #print(type(im))
            


class MainWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Camera Feed")
        #self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight = 600
        self.setFixedWidth = 800

        self.image = QPixmap()
        self.label = QLabel()
        self.grid = QGridLayout()
        self.grid.addWidget(self.label,0,0)
        self.setLayout(self.grid)

        self.video_thread = VideoThread(self)
        self.video_thread.change_pixmap.connect(self.set_image)
        self.video_thread.start()

        

    def set_image(self, image):
        self.label.setPixmap(QPixmap(image))
        


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
