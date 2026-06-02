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

    #RK4 UPDATE FUNCTION
    def step_rk4(self, dt):
        a = self.a.copy()
        k1_r = self.v
        k1_v = a
        k2_r = self.v + 0.5*dt*k1_v
        k2_v = a
        k3_r = self.v + 0.5*dt*k2_v
        k3_v = a
        k4_r = self.v + dt*k3_v
        k4_v = a
        self.r += (dt/6.0)*(k1_r + 2*k2_r + 2*k3_r + k4_r)
        self.v += (dt/6.0)*(k1_v + 2*k2_v + 2*k3_v + k4_v)

    #MOTION MODELS

    #CONSTANT VELOCITY
    def constant_velocity(self, dt):
        self.r += self.v * dt
        self.a[:] = 0.0
    
    #CONSTANT ACCELERATION
    def constant_acceleration(self, dt):
        #ACCELERATION FROM IC PARAMS
        self.a[:] = np.array(self.params['accel'], dtype = float)
        #UPDATE VELOCITY AND POSITION
        self.step_rk4(dt)
    
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
        
        #UPDATE VELOCITY AND POSITION
        self.step_rk4(dt)
    
    #UPDATE FUNCTION 
    def update(self, dt):
        if self.motion_type == "constant_velocity":
            self.constant_velocity(dt)
        elif self.motion_type == "constant_acceleration":
            self.constant_acceleration(dt)
        elif self.motion_type == "weaving":
            self.weaving(dt)
        
        self.time += dt
        
