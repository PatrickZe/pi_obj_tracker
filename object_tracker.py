#General imports
import sys
import time



#Custom imports
from servos_pid import Tracker_Servos
import color_detection
import person_detection

########################
#Duty cycles: 
#	Rotation: 	2.5 - 12.5
# 	Tilt: 		2.5 - 9.5
########################



#Main code
if __name__ == "__main__":
	mech_rotation = Tracker_Servos(18)
	mech_rotation.set_dc_boundary(2.5, 12.5)

	mech_tilt = Tracker_Servos(13)
	mech_tilt.set_dc_boundary(2.5, 9.5)
	
	#for i in range(0,150,1):
	#	mech_tilt._set_dc_values(i/10)
	#	mech_rotation._set_dc_values(i/10)
	#	time.sleep(0.02)

	mech_tilt._set_dc_values(7.5)
	mech_rotation._set_dc_values(7.5)	
	time.sleep(10)
	#mech_tracker._set_pwm_values(2.5, 2.5)
	#time.sleep(3)
	#mech_tracker._set_pwm_values(12.5, 9.5)
	#time.sleep(3)
	
