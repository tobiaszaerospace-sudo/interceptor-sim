import numpy as np

class Target:
    #INITIALIZE TARGET AND MODE AND PARAMETERS
    def __init__(self, r0, v0, motion_type='constant_velocity', params = None):
        self.r = np.array(r0, dtype=float)
        self.v = np.array(v0, dtype=float)
        self.a = np.zeros(3)
        self.motion_type = motion_type
        self.params = params if params is not None else {}
        self.time = 0.0

    #MOTION MODELS

    #CONSTANT VELOCITY
    def constant_velocity(self, dt):
        self.r += self.v * dt
        self.a[:] = 0.0
    
    #CONSTANT ACCELERATION
    def constant_acceleration(self, dt):
        #ACCELERATION FROM IC PARAMS
        self.a[:] = np.array(self.params['accel'], dtype = float)
        #UPDATE VELOCITY
        self.v += self.a*dt
        #UPDATE POSITION
        self.r += self.v*dt
    
    #WEAVING MOTION MODEL
    def weaving(self, dt):
        #MAKE VARIABLES LOCAL SO IT'S EASIER TO WRITE
        A = self.params['amplitude']
        W = self.params['omega']
        axis = self.params['axis']

        #USE SIN LATERAL ACCELERATION FORMULA
        a_val = A * np.sin(W*self.time)

        #RESET ACCELERATION VECTOR SO WE CAN ALTER FOR CHOSEN AXIS
        self.a[:] = 0.0
        #NOW ALTER FOR CHOSEN AXIS
        if axis == 'x':
            self.a[0] = a_val
        elif axis == 'y':
            self.a[1] = a_val
        else:
            self.a[2] = a_val
        
        #UPDATE VELOCITY
        self.v += self.a*dt
        
        #UPDATE POSITION
        self.r += self.v*dt
    
    #UPDATE FUNCTION 
    def update(self, dt):
        if self.motion_type == "constant_velocity":
            self.constant_velocity(dt)
        elif self.motion_type == "constant_acceleration":
            self.constant_acceleration(dt)
        elif self.motion_type == "weaving":
            self.weaving(dt)
        
        self.time += dt
        
