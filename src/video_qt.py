from picamera2 import Picamera2, MappedArray
from picamera2.previews.qt import QGlPicamera2
from libcamera import Transform
from PyQt5.QtCore import QThread, pyqtSignal

import cv2
import numpy as np
from pathlib import Path
import logging
import time
from collections import deque
#Tensorflow
import tflite_runtime.interpreter as tflite


class VideoThread(QThread):
    new_aktor_data_available = pyqtSignal(int)

    def __init__(self, tilt, rotation,  parent=None):
        QThread.__init__(self, parent=parent)
        #Vars
        self.pixel_delta_x = 0
        self.pixel_delta_y = 0

        self.faces = []
        self.colors = []
        self.persons = []
        self.last_time = time.time()
        self.avg_fps = deque([0,0,0,0,0])
        self.mode = "Raw"

        #aktors:
        self.tilt_mechanic = tilt
        self.rotation_mechanic = rotation
        #Setup Opencv
        self.face_detector_cv = cv2.CascadeClassifier("/home/patrick/Projects/pi_obj_tracker/src/haarcascade_frontalface_default.xml")
        
        #setup picamera
        self.picam2 = Picamera2()
        #main & low resulution, cam mounted upside down
        config = self.picam2.create_preview_configuration(   main={"size": (640, 480)},
                                                        lores={"size": (320, 240), "format": "YUV420"}, 
                                                        transform=Transform(vflip=1))
        self.picam2.configure(config)

        (self.w0, self.h0) = self.picam2.stream_configuration("main")["size"]
        (self.w1, self.h1) = self.picam2.stream_configuration("lores")["size"]
        self.s1 = self.picam2.stream_configuration("lores")["stride"]

        self.qtcam = QGlPicamera2(self.picam2, width=640, height=480, keep_ar=True)

        
        #setup tensorflow
        self.tf_labels = self.read_tfl_label_file()
        self.tfl_model = str(Path(__file__).with_name("mobilenet_v2.tflite"))
        self.setup_tfl_interpreter()

        self.picam2.start()




    def run(self):
        #Mainloop: go throug the selected mode as fast as possible
        while True:

            if self.mode == "Raw":
                #self.show_raw()
                pass

            elif self.mode == "OpenCV face":
                buffer = self.picam2.capture_buffer("lores")
                grey = buffer[:self.s1 * self.h1].reshape((self.h1, self.s1))
                self.faces = self.face_detector_cv.detectMultiScale(grey, 1.1, 3)
            
            elif self.mode == "OpenCV color":
                buffer = self.picam2.capture_array("lores")
                bgr = cv2.cvtColor(buffer, cv2.COLOR_YUV420p2BGR) 
                hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV) 
                self.colors = self.color_detector_cv(hsv)
            
            elif self.mode == "TFL person":
                buffer = self.picam2.capture_buffer("lores")
                grey = buffer[:self.s1 * self.h1].reshape((self.h1, self.s1))
                self.persons = self.tfl_interference_person(grey)

            else:
                pass

            #calculate the new average fps to show
            fps = 1/(time.time()-self.last_time)
            self.avg_fps.append(fps)
            self.avg_fps.popleft()
            self.fps = sum(self.avg_fps)/len(self.avg_fps)
            self.last_time = time.time()



    def read_tfl_label_file(self):
        #read the label file needed to operate tensorflow
        file = Path(__file__).with_name("tf_labels.txt")

        with file.open('r') as f:
            lines = f.readlines()
        ret_val = {}
        for line in lines:
            #format: index label (e.g. 0 person)
            pair = line.strip().split(maxsplit=1)
            ret_val[int(pair[0])] = pair[1].strip()
        return ret_val


    def get_cam(self):
        return self.qtcam

    def switch_mode(self, new_mode: str):
        #switch between the different operation modes
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
            self.picam2.post_callback = self.draw_persons_tfl
            self.mode = new_mode
            pass
        else:
            logging.warn("Mode not recognized!")
        
    def empty_callback(self, request):
        #placeholder, for raw-mode
        pass

    def setup_tfl_interpreter(self):
        # Setup the tensorflow interpreter as shown in the docs
        self.tfl_interpreter = tflite.Interpreter(model_path=self.tfl_model, num_threads=4)
        self.tfl_interpreter.allocate_tensors()

        self.tf_input_details = self.tfl_interpreter.get_input_details()
        self.tf_output_details = self.tfl_interpreter.get_output_details()

        self.tf_height = self.tf_input_details[0]['shape'][1]
        self.tf_width = self.tf_input_details[0]['shape'][2]

        self.floating_model = False
        if self.tf_input_details[0]['dtype'] == np.float32:
            self.floating_model = True


    def tfl_interference_person(self, grey_img):

        #image details
        rgb = cv2.cvtColor(grey_img, cv2.COLOR_GRAY2RGB)
        initial_h, initial_w, channels = rgb.shape

        #Resize to tf model size
        picture = cv2.resize(rgb, (self.tf_width, self.tf_height))

        input_data = np.expand_dims(picture, axis=0)
        if self.floating_model:
            input_data = (np.float32(input_data) - 127.5) / 127.5

        #Starting tfl_interpreter
        self.tfl_interpreter.set_tensor(self.tf_input_details[0]['index'], input_data)

        self.tfl_interpreter.invoke()

        #get tf output
        detected_boxes = self.tfl_interpreter.get_tensor(self.tf_output_details[0]['index'])
        detected_classes = self.tfl_interpreter.get_tensor(self.tf_output_details[1]['index'])
        detected_scores = self.tfl_interpreter.get_tensor(self.tf_output_details[2]['index'])
        num_boxes = self.tfl_interpreter.get_tensor(self.tf_output_details[3]['index'])

        rectangles = []
        for i in range(int(num_boxes)):
            top, left, bottom, right = detected_boxes[0][i]
            classId = int(detected_classes[0][i])
            score = detected_scores[0][i]
            if score > 0.5 and classId == 0: #classId 0 == person
                xmin = int(left * initial_w)
                ymin = int(bottom * initial_h)
                xmax = int(right * initial_w - xmin)
                ymax = int(top * initial_h - ymin)
                box = [xmin, ymin, xmax, ymax]
                rectangles.append(box)
                
                #print(labels[classId], 'score = ', score)
                rectangles[-1].append(self.tf_labels[classId])


        return rectangles
                
            


    def draw_persons_tfl(self, request):
        with MappedArray(request, "main") as m:
            #fps overlay
            text = f"{self.fps:.2f} fps"
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(m.array, text, (20,30), font, 1, (255, 255, 255), 2, cv2.LINE_AA)

            #tfl overlay
            for person in self.persons:

                (x,y,w,h) = person[:4]
                x = x*2
                y = y*2
                w = w*2
                h = h*2
                cv2.rectangle(m.array, (x,y), (x + w, y + h), (0,255,0,0))

                if len(self.persons) == 1:
                    self.get_pixel_delta_from_mid(x+0.5*w, y+0.5*h)
                    self.new_aktor_data_available.emit(1)
                    
                    return
                else:
                    logging.warn(f"{len(self.persons)} persons detected.")
                    return
                
            return
    

    def draw_color_cv(self, request):
        
        with MappedArray(request, "main") as m:
            #fps overlay
            text = f"{self.fps:.2f} fps"
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(m.array, text, (20,30), font, 1, (255, 255, 255), 2, cv2.LINE_AA)

            #opencv overlay
            for cont in self.colors:
                (x,y,w,h) = cont
                x = x*2
                y = y*2
                w = w*2
                h = h*2
                cv2.rectangle(m.array, (x, y), (x + w, y + h), (0, 255, 0, 0))

                #only one rectangle to draw
                if len(self.colors) == 1:
                    self.get_pixel_delta_from_mid(x+0.5*w, y+0.5*h)
                    self.new_aktor_data_available.emit(1)
                    return 
                #too many/no rectangles
                else: 
                    return
                    
                    

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
        
        with MappedArray(request, "main") as m:
            #fps overlay
            text = f"{self.fps:.2f} fps"
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(m.array, text, (20,30), font, 1, (255, 255, 255), 2, cv2.LINE_AA)

            #opencv overlay
            
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


    def show_opencv_face(self):
        #OpenCV Face
        #start_time = time.time()
        image = self.picam2.capture_array()
        grey = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_detector_cv.detectMultiScale(grey, 1.1, 5)

        for (x, y, w, h) in faces:
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0))
        self.translate_and_emit_image(image)