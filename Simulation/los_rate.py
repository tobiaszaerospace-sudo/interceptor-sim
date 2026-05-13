import numpy as np

#USING SINGLE FUNCTION FOR THIS, NO NEED FOR CLASS
def compute_los_rate(r_rel, v_rel, Range):
    #COMPUTE LOS RATE USING FOMULA FROM PAPER

    #AVOID DIVIDING BY ZEROS
    if Range == 0:
        return np.zeros(3)
    
    #CROSS PRODUCT FORMULA FOR LOS RATE
    los_rate = np.cross(r_rel, v_rel) / (Range**2)

    return los_rate