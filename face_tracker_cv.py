
import time
import cv2
from picamera2 import MappedArray, Picamera2, Preview
from libcamera import Transform
from servos_pid import Tracker_Servos


face_detector = cv2.CascadeClassifier("/home/patrick/dep/opencv/haarcascade_frontalface_default.xml")
face_x = 0
face_y = 0
pixel_delta_x = 0
pixel_delta_y = 0


def draw_faces(request):
	with MappedArray(request, "main") as m:
		for f in faces:
			(x, y, w, h) = [c * n // d for c, n, d in zip(f, (w0, h0) * 2, (w1, h1) * 2)]
			cv2.rectangle(m.array, (x, y), (x + w, y + h), (0, 255, 0, 0))
			get_pixel_delta_from_mid(x+0.5*w, y+0.5*h)
            

def get_pixel_delta_from_mid(pixel_x: int, pixel_y: int):
	global pixel_delta_x, pixel_delta_y
	size_x = 640
	size_y = 480
	
	pixel_delta_x = pixel_x - 0.5*size_x
	pixel_delta_y = pixel_y - 0.5*size_y
	


#Setup camera
picam2 = Picamera2()
picam2.start_preview(Preview.QT)
config = picam2.create_preview_configuration(main={"size": (640, 480)},
                                             lores={"size": (320, 240), "format": "YUV420"}, 
                                             transform=Transform(vflip=1))
picam2.configure(config)

(w0, h0) = picam2.stream_configuration("main")["size"]
(w1, h1) = picam2.stream_configuration("lores")["size"]
s1 = picam2.stream_configuration("lores")["stride"]

faces = []
picam2.post_callback = draw_faces

picam2.start()

#Setup mechanics	mech_rotation = Tracker_Servos(18)
mech_rotation = Tracker_Servos(18)
mech_rotation.set_dc_boundary(2.5, 12.5)

mech_tilt = Tracker_Servos(13)
mech_tilt.set_dc_boundary(2.5, 9.5)
	

mech_tilt._set_dc_values(6.5)
mech_rotation._set_dc_values(7.5)	


start_time = time.time()
while True:
	buffer = picam2.capture_buffer("lores")
	grey = buffer[:s1 * h1].reshape((h1, s1))
	faces = face_detector.detectMultiScale(grey, 1.1, 3)
	if True:#time.time()-start_time > 0.2:
		#print(f"Face at x={pixel_delta_x}, y={pixel_delta_y}")
		#print(faces)
		mech_rotation.set_pixel_delta(pixel_delta_x)
		mech_tilt.set_pixel_delta(pixel_delta_y)
		#print(f"dT = {time.time()-start_time}")
		start_time = time.time()
		
