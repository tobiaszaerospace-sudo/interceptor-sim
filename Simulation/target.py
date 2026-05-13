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