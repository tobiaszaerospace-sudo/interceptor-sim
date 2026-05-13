import numpy as np

#USING SINGLE FUNCTION FOR THIS, NO NEED FOR ANY CLASS
def compute_relative_kinematics(target, interceptor):
    #RELATIVE POSITION AND VELOCITY
    r_rel = target.r - interceptor.r
    v_rel = target.v - interceptor.v

    #COMPUTE RANGE(MAGNITUDE EQUATION)
    Range = np.sqrt((r_rel[0])**2+(r_rel[1])**2+(r_rel[2])**2)

    #FOR ZERO RANGE 
    if Range == 0:
        r_hat = np.zeros(3)
        Vc = 0.0
        return r_rel, v_rel, Range, r_hat, Vc
    
    #LOS UNIT VECTOR
    r_hat = r_rel / Range

    #CLOSING VELOCITY 
    Vc = -np.dot(v_rel, r_hat)

    return r_rel, v_rel, Range, r_hat, Vc