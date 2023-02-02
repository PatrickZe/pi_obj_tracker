
#!/usr/bin/env python

from PyQt5.QtCore import *#QDateTime, Qt, QTimer, pyqtSlot
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QDateTimeEdit,
        QDial, QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
        QProgressBar, QPushButton, QRadioButton, QScrollBar, QSizePolicy,
        QSlider, QSpinBox, QStyleFactory, QTableWidget, QTabWidget, QTextEdit,
        QVBoxLayout, QWidget, QButtonGroup)

import sys


class GUI_Thread(QThread):

    def run(self):
        app = QApplication(sys.argv)
        gallery = MainGUI()
        gallery.show()
        sys.exit(app.exec_())
 


class MainGUI(QDialog):
    def __init__(self, cam, parent=None):
        super(MainGUI, self).__init__(parent)

        ###VARS
        self.controll_mode = "Manual"
        self.algo_mode = "Raw"

        self.originalPalette = QApplication.palette()


        self.create_man_auto_group_box()
        self.create_algorithm_group_box()
        self.create_manual_sliders()
        #self.createTopRightGroupBox()
        #self.createBottomLeftTabWidget()
        #self.createBottomRightGroupBox()

        topLayout = QHBoxLayout()
        #topLayout.addWidget(styleLabel)
        #topLayout.addWidget(styleComboBox)
        topLayout.addStretch(1)
        #topLayout.addWidget(self.useStylePaletteCheckBox)
        #topLayout.addWidget(disableWidgetsCheckBox)

        mainLayout = QGridLayout()
        mainLayout.addLayout(topLayout, 0, 0, 1, 2)
        mainLayout.addWidget(self.man_auto_group_box, 0, 0)
        mainLayout.addWidget(self.algorithm_group_box, 1, 0 )
        mainLayout.addWidget(self.manual_sliders, 1, 1)
        cam.setFixedWidth(640)
        cam.setFixedHeight(480)
        mainLayout.addWidget(cam, 0,1)
        #mainLayout.addWidget(self.topRightGroupBox, 1, 1)
        #mainLayout.addWidget(self.bottomLeftTabWidget, 2, 0)
        #mainLayout.addWidget(self.bottomRightGroupBox, 2, 1)
        #mainLayout.addWidget(self.progressBar, 3, 0, 1, 2)
        mainLayout.setRowStretch(1, 1)
        mainLayout.setRowStretch(2, 1)
        mainLayout.setColumnStretch(0, 1)
        mainLayout.setColumnStretch(1, 1)
        self.setLayout(mainLayout)

        self.setWindowTitle("Object Tracker")
        



    def create_man_auto_group_box(self):
        self.man_auto_group_box = QGroupBox("Controll Mode")
        radio_auto = QRadioButton("Automatic")
        radio_manual = QRadioButton("Manual")

        radio_manual.setChecked(True)

        self.man_auto_button_group = QButtonGroup()
        self.man_auto_button_group.addButton(radio_auto, 2)
        self.man_auto_button_group.addButton(radio_manual, 1)

        self.man_auto_button_group.buttonClicked.connect(self.change_man_auto_mode)

        layout = QVBoxLayout()
        layout.addWidget(radio_manual)
        layout.addWidget(radio_auto)
        layout.addStretch(1)
        self.man_auto_group_box.setLayout(layout)

    def create_algorithm_group_box(self):
        self.algorithm_group_box = QGroupBox("Tracking Algorithm")
        raw = QRadioButton("Raw Image")
        opencv_color = QRadioButton("OpenCV color")
        opencv_face = QRadioButton("OpenCV face")
        tensorflow_person = QRadioButton("Tensorflow person")



        raw.setChecked(True)

        self.algorithm_button_group = QButtonGroup()
        self.algorithm_button_group.addButton(raw, 1)
        self.algorithm_button_group.addButton(opencv_color, 2)
        self.algorithm_button_group.addButton(opencv_face, 3)
        self.algorithm_button_group.addButton(tensorflow_person, 4)

        layout = QVBoxLayout()
        layout.addWidget(raw)
        layout.addWidget(opencv_color)
        layout.addWidget(opencv_face)
        layout.addWidget(tensorflow_person)

        layout.addStretch(1)
        self.algorithm_group_box.setLayout(layout)



 


    def create_manual_sliders(self):
        self.manual_sliders = QGroupBox("Manual Sliders")


        slider = QSlider(Qt.Orientation.Horizontal, self.manual_sliders)
        slider.setValue(40)


        layout = QGridLayout()

        layout.addWidget(slider, 3, 0)
        layout.setRowStretch(5, 1)
        self.manual_sliders.setLayout(layout)

    def change_man_auto_mode(self, object):
        id = self.man_auto_button_group.id(object) #1=Manual, 2 = Auto
        print(f"ID: {id}")
        if id == 1:
            self.controll_mode = "Manual"
        else:
            self.controll_mode = "Automatic"

    def change_algorithm(self, object):
        id = self.algorithm_button_group.id(object) #1=Raw, 2=CV color, 3= cv face, 4=tfl
        if id == 1:
            self.algo_mode = "Raw"
        elif id == 2:
            self.algo_mode = "OpenCV color"
        elif id == 3:
            self.algo_mode = "OpenCV face"
        elif id == 4:
            self.algo_mode = "TFL person"
        else:
            pass#should not happen



#if __name__ == '__main__':
#
#    import sys
#
#    app = QApplication(sys.argv)
#    gallery = MainGUI()
#    gallery.show()
#    sys.exit(app.exec_())
