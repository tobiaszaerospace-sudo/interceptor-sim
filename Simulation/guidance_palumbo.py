import numpy as np

#GUIDANCE CLASS FOR PN, APN, AND ZEM
class Guidance:
    #INITIALIZE VALUES
    def __init__(self, N=3.0, N_zem = 3.0):
        self.N = N #NAVIGATION CONSTANT FOR PN/APN
        self.N_zem = N_zem #NAVIGATION CONSTANT FOR ZERO EFFORT MISS BASED GUIDANCE

    #PURE PROPORTIONAL NAVIGATION (PURE PN)
    def pn(self, r_hat, Vc, los_rate_vec):
        #FORMULA FROM PAPER
        return self.N*Vc*np.cross(los_rate_vec, r_hat)
    
    #AUGMENTED PROPORTIONAL NAVIGATION (APN)
    def apn(self, r_hat, Vc, los_rate_vec, a_target):
        #FORMULAS FROM ZARCHAN PAPER
        a_pn = self.pn(r_hat, Vc, los_rate_vec)
        a_t_parallel = np.dot(a_target, r_hat) * r_hat
        a_t_perp = a_target - a_t_parallel
        #BASIC APN FORMULA, PURE PN PLUS ACCELERATION VALUE DERIVATION TERMS
        return a_pn + .5 * self.N * a_t_perp
    
    #ZERO EFFORT MISS
    def compute_zem(self, r_rel, v_rel, a_target, t_go):
        return r_rel + v_rel * t_go + .5 * a_target * (t_go**2)

    def zem_guidance(self, r_rel, v_rel, a_target, Vc, Range):
        #AVOID OVERSHOOT OR CORRECTION AT INTERCEPTION POINT
        if Range == 0 or Vc <= 0:
            return np.zeros(3)
        #TIME LEFT
        t_go = Range/Vc
        #ZEM VALUE
        zem = self.compute_zem(r_rel, v_rel, a_target, t_go)
        #LOS UNIT VECTOR
        r_hat = r_rel/Range
        #DROP LOS COMPONENT, LOOK AT LATERAL ZEM(FIX TO TARGET NORMAL)
        zem_parallel = np.dot(zem, r_hat)*r_hat
        zep_perp = zem-zem_parallel
        #ZERO EFFORT MISS GUIDANCE OUTPUT
        return self.N_zem * zep_perp / (t_go**2)
