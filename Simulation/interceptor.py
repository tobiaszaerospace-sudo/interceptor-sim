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
    def step_rk4(self, dt):
        #K1 CALCULATIONS
        v1 = self.v
        a1 = self.a

        #K2 CALCULATIONS
        v2 = self.v + .5*dt*a1
        a2 = self.a

        #K3 CALCULATIONS
        v3 = self.v + .5*dt*a2
        a3 = self.a

        #K4 CALCULATIONS
        v4 = self.v + dt*a3
        a4 = self.a

        #COMBINE K1-K4 TO UPDATE POSITION AND VELOCITY
        self.r += (dt/6)*(v1 + 2*v2 + 2*v3 + v4)
        self.v += (dt/6)*(a1 + 2*a2 + 2*a3 + a4)