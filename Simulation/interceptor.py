import numpy as np

class Interceptor:
    #INITIALIZE VALUES FOR INTERCEPTOR
    def __init__(self, r0, v0):
        self.r = np.array(r0, dtype=float)  # Position vector
        self.v = np.array(v0, dtype=float)  # Velocity vector
        self.a = np.zeros(3)                # Acceleration vector
    
    #SETS INTERCEPTORS ACTUAL ACCELERATION VECTOR - FROM AUTOPILOT ALGORITHM
    def set_acceleration(self, a_vector):
        self.a = np.array(a_vector, dtype=float)
    
    #EULER PREDICTION FOR SIMPLE MOTION UPDATE
    def step_euler(self, dt):
        self.r += self.v*dt
        self.v += self.a*dt
    
    #RUNGE-KUTTA 4TH ORDER METHOD FOR MORE ACCURATE MOTION UPDATE
    def step_rk4(self, dt, a):
        a = np.array(a, dtype = float)
        #K1 CALCULATIONS
        k1_r = self.v
        k1_v = a

        #K2 CALCULATIONS
        k2_r = self.v + .5*dt*k1_v
        k2_v = a

        #K3 CALCULATIONS
        k3_r = self.v + .5*dt*k2_v
        k3_v = a

        #K4 CALCULATIONS
        k4_r = self.v + dt*k3_v
        k4_v = a

        #COMBINE K1-K4 TO UPDATE POSITION AND VELOCITY
        self.r += (dt/6)*(k1_r + 2*k2_r + 2*k3_r + k4_r)
        self.v += (dt/6)*(k1_v + 2*k2_v + 2*k3_v + k4_v)