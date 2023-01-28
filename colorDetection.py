#screwdriver: hsv(350, 94, 91)

import cv2
import numpy as np
import time
color = np.uint8([[[15,93,77]]])
hsv_color = cv2.cvtColor(color, cv2.COLOR_BGR2HSV)
 
hue = hsv_color[0][0][0]
print(hsv_color)
print(hue)

start_time = time.time()
# Read the picure - The 1 means we want the image in BGR
img = cv2.imread('can.png', 1) 

# resize imag to 20% in each axis
img = cv2.resize(img, (0,0), fx=0.2, fy=0.2)
# convert BGR image to a HSV image
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV) 

# NumPy to create arrays to hold lower and upper range 
# The “dtype = np.uint8” means that data type is an 8 bit integer

lower_range = np.array([70, 100, 100], dtype=np.uint8) 
upper_range = np.array([120, 255, 255], dtype=np.uint8)

# create a mask for image
mask = cv2.inRange(hsv, lower_range, upper_range)

#define kernel size  
kernel = np.ones((7,7),np.uint8)

# Remove unnecessary noise from mask

mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
print(f"Finished in {time.time()-start_time} seconds.")

# display both the mask and the image side-by-side
cv2.imshow('mask',mask)
cv2.imshow('image', img)

# wait to user to press [ ESC ]
while(1):
  k = cv2.waitKey(0)
  if(k == 27):
    break
 
cv2.destroyAllWindows()
