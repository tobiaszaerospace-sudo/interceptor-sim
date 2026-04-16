#PURPOSE IS TO DEFINE THE STATE DICTIONARY/STATE OBJECT
import numpy as np

class State:
    def __init__(self):
        #NOTES
        #ZEROS(3) IS FOR A 1X3 VECTOR, FOR X Y AND Z VALUES IN THEIR RESPECTIVE SECTION
        #TARGET IS FOR TARGET
        #INT IS FOR INTERCEPTOR

        #POSITIONS
        self.target_pos = np.zeros(3)
        self.int_pos = np.zeros(3)

        #VELOCITIES
        self.target_vel = np.zeros(3)
        self.int_vel = np.zeros(3)

        #ORIENTATION (EULER OR QUATERNION)
        self.int_orientation = np.zeros(3)

        #ANGULAR RATES
        self.int_omega = np.zeros(3)

        #TIME
        self.t=0.0
#LINK SIMULATION AND CAMERA

#DEFINE STATE LIBRARY