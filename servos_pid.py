import RPi.GPIO as gpio

import pigpio

class PID():
	def __init__(self):
		self.mode = "P"
		self.Kp = 0.001 #should be <<1
		pass
		
	#Internal
	def _proportional(self, pixel_error: int)->float:
		return pixel_error*self.Kp
		
	def _integral(self)->None:
		#Maybe not as important
		pass

	def _differential(self)->None:
		#Maybe not as important
		pass
	
	
	#External
	def set_mode(self, mode: str)->None:
		#No switch for now, P should be enough
		self.mode = "P"
		
	def get_new_duty_cycle_offset(self, pixel_error: int)->float:
		if self.mode == "P":
			return self._proportional(pixel_error)
			
		#TODO: other modes
		else: 
			return 0
	
		

class Tracker_Servos():
	def __init__(self, servopin: int)->None:
		#init the pins
		#Servo 1: base rotation
		#Servo 2: midsection tilting
		#gpio.setmode(gpio.BCM)
		#gpio.setup(servopin, gpio.OUT)
		self.servopin = servopin
		
		self._current_dc = 1.5

		#Set up PID controller
		self._pid = PID()
		
		#Set the pins to starting 
		#self._servo = gpio.PWM(servopin, 50) #50 Hz
		
		#Start Servos in neutral position
		#self._servo.start(self._current_dc)
		
		#alternative with pigpio
		self.gpio = pigpio.pi()

		
	#Internal
	def _set_dc_values(self, dc: float)->None:
		#Sets the new dc values
		new_dc = -1
		
		#Switch wished/min/max value
		if self._lower_bound <= dc and dc <= self._upper_bound:
			#normal operation
			new_dc = dc
		elif self._lower_bound >= dc:
			#set minumum possible
			new_dc = self._lower_bound
		elif dc >= self._upper_bound:
			#set maximum possible
			new_dc = self._upper_bound
		else:
			#value not permitted
			pass
		#Chang dc

		self.gpio.hardware_PWM(self.servopin, 50, int(new_dc*10000))
		#self._servo.ChangeDutyCycle(new_dc)
		self._current_dc = new_dc
		

	
	#external
	def set_pixel_delta(self, delta: int)->None:
		#Picture:
		########################################
		#negative dx,dy
		#
		#
		#
		#
		#                         positive dx,dy
		########################################
		pid_dc_offset = self._pid.get_new_duty_cycle_offset(delta)
		self._set_dc_values(self._current_dc + pid_dc_offset)

		
	def set_dc_boundary(self, servo_lower: int, servo_upper: int)->None:
		#Sets the duty cycle boundarys
		#PWM duty cycle in %
		self._lower_bound = servo_lower
		self._upper_bound = servo_upper
