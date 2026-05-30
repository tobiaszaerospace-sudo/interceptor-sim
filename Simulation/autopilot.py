#CALLED AUTOPILOT BUT IS REALLY A CONTROL LOOP FOR ACCELERATION
import numpy as np

class Autopilot:
    #INITIALIZZE AUTOPILOT TAU IS A FIRST ORDER LAG TIME CONSTANT
    def __init__(self, max_accel = None, tau = 0.1):
        self.max_accel = max_accel
        #VALIDATE TIME CONSTANT
        while tau is None or tau <= 0:
            try:
                tau = float(input("Enter a positive tau value: "))
            except ValueError:
                print("Invalid input. Please enter a numeric value.")
                tau = None #force loop to continue
        self.tau = tau
        self.a_actual = np.zeros(3)
    
    #APPLY ACCELERATION LIMIT
    def apply_accel_limit(self,a_command):
        #IF THERE'S NO ACCELERATION LIMIT, DON'T APPLY ONE
        if self.max_accel is None:
            return a_command
        #IF THE COMMANDED ACCELERATION IS LESS THAN THE MAX, GIVE THE COMMANDED ACCELERATION
        magnitude = np.sqrt((a_command[0])**2 + (a_command[1])**2 + (a_command[2])**2)
        if magnitude == 0 or magnitude <= self.max_accel:
            return a_command
        #IF COMMANDED ACCELERATION IS BIGGER, RETURN MAX ACCELERATION POSSIBLE WITH RESPECT TO DIRECTION VECTOR
        return self.max_accel * (a_command/magnitude)
    
    #UPDATE
    def update(self, a_command, dt):
        #APPLY ACCELERATION LIMITS
        a_command_limited = self.apply_accel_limit(a_command)
        #FIRST ORDER LAG FROM PAPER CONVERTED FROM LOS/SPHERICAL TO CARTESIAN
        alpha = dt/self.tau
        self.a_actual += alpha * (a_command_limited - self.a_actual)
        #RETURN ADJUSTED ACCELERATION VALUE IF ADJUSTED AT ALL
        return self.a_actual.copy()
