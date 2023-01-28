import time
import cv2
from picamera2 import MappedArray, Picamera2, Preview

face_detector = cv2.CascadeClassifier("/home/patrick/dep/opencv/haarcascade_frontalface_default.xml")
face_x = 0
face_y = 0

def draw_faces(request):
	with MappedArray(request, "main") as m:
		for f in faces:
			(x, y, w, h) = [c * n // d for c, n, d in zip(f, (w0, h0) * 2, (w1, h1) * 2)]
			cv2.rectangle(m.array, (x, y), (x + w, y + h), (0, 255, 0, 0))
			global face_x, face_y
			face_x = int(x + 0.5*w)
			face_y = int(y + 0.5*h)
            


#Setup camera
picam2 = Picamera2()
picam2.start_preview(Preview.QT)
config = picam2.create_preview_configuration(main={"size": (640, 480)},
                                             lores={"size": (320, 240), "format": "YUV420"})
picam2.configure(config)

(w0, h0) = picam2.stream_configuration("main")["size"]
(w1, h1) = picam2.stream_configuration("lores")["size"]
s1 = picam2.stream_configuration("lores")["stride"]

faces = []
picam2.post_callback = draw_faces

picam2.start()

start_time = time.time()
while True:
	buffer = picam2.capture_buffer("lores")
	grey = buffer[:s1 * h1].reshape((h1, s1))
	faces = face_detector.detectMultiScale(grey, 1.1, 3)
	if time.time()-start_time > 3:
		print(f"Face at x={face_x}, y={face_y}")
		start_time = time.time()

