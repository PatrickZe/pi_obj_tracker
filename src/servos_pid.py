import RPi.GPIO as gpio
import logging
import pigpio

class PID():
	"""Simple PID implementation. Not a exact mathematical representation!
	"""
	def __init__(self):
		self.mode = "P"
		self.Kp = 0.001 #should be <<1
		self.Ki = 0.0005
		self.Kd = 0.00001

		#previous
		self.prev_error = 0
		self.integral_val = 0
		
	#Internal
	def _proportional(self, pixel_error: int)->float:
		return pixel_error*self.Kp
		
	def _integral(self, pixel_error: int, dt: float)->float:
		return self.Ki * (self.integral_val+ pixel_error*dt)

	def _differential(self, pixel_error: int, dt: float)->float:
		#Not as important
		return self.Kd * (pixel_error-self.prev_error) / dt
	 
	
	#External
	def set_mode(self, mode: str)->None:
		# Deprecated 
		#No switch for now, P should be enough
		self.mode = "P"
		
	def get_new_duty_cycle_offset(self, pixel_error: int, mode: str="P", dt: float=0)->float:
		# Calculates the new dc offset based on the pixels and mode

		ret_val = 0
		if "P" in mode:
			ret_val = ret_val + self._proportional(pixel_error)
		if "I" in mode:
			ret_val = ret_val + self._integral(pixel_error, dt)
		if "D" in mode: 
			ret_val = ret_val + self._differential(pixel_error, dt)
		
		return float(ret_val)
			
	
		

class Tracker_Servos():
	def __init__(self, servopin: int)->None:
		# Handler class for the servos.
		# use only Hardware-PWM pins for smooth operation
		
		self.servopin = servopin

		#Set up PID controller
		self._pid = PID()
		
		self.gpio = pigpio.pi()

		#initial, safe boundarys
		self.set_dc_boundary(5, 6)
		#initial, safe duty cycle
		self._current_dc = 5.5
		self._set_dc_values(self._current_dc)

		
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
		

		#Set the new dc
		self.gpio.hardware_PWM(self.servopin, 50, int(new_dc*10000))
		self._current_dc = new_dc
		

	
	#external
	def set_pixel_delta(self, delta: int, dt: float=0)->None:
		#Picture:
		########################################
		#negative dx,dy
		#
		#
		#
		#
		#                         positive dx,dy
		########################################
		if abs(delta) > 20:
			#print(delta)
			if dt > 0:
				#full PID possible
				pid_dc_offset = self._pid.get_new_duty_cycle_offset(delta, "PID", dt)
			else:
				#only P makes sense
				pid_dc_offset = self._pid.get_new_duty_cycle_offset(delta)

			self._set_dc_values(self._current_dc + pid_dc_offset)

		
	def set_dc_boundary(self, servo_lower: int, servo_upper: int)->None:
		#Sets the duty cycle boundarys
		#PWM duty cycle in %
		self._lower_bound = servo_lower
		self._upper_bound = servo_upper

	def set_angle(self, angle:float) -> None:
		#90° = 5%
		dc = 7.5 + angle*(5/90)

		self._set_dc_values(dc)
