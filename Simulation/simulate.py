#IMPORT LIBRARY
import numpy as np
#IMPORT ALL OTHER FILES
from initial_conditions import InitialConditions
from target import Target
from interceptor import Interceptor
from autopilot import Autopilot
from guidance_palumbo import Guidance
from relative_kinematics import compute_relative_kinematics
from los_rate import compute_los_rate

#SIMULATION FUNCTION
def run_simulation(guidance_mode, dt, t_max, kill_radius, max_accel, tau, N):
    #RUNS A SINGLE SIMULATION WITH GUIDANCE LAW, WILL RETURN DICTIONARY

    #INITIAL CONDITIONS
    ic = InitialConditions()
    ri0, vi0 = ic.build_interceptor()
    rt0, vt0, motion_type, params = ic.build_target()

    #OBJECTS
    target = Target(rt0, vt0, motion_type, params)
    interceptor = Interceptor(ri0, vi0)
    guidance = Guidance(N=N)
    autopilot = Autopilot(max_accel = max_accel, tau = tau)

    #LOGGING
    t = 0.0
    hit = False
    accel_log = []
    time_log = []
    range_log = []
    interceptor_pos_log = []
    target_pos_log = []

    #START LOOP
    while t < t_max:

        #RELATIVE KINEMATICS
        r_rel, v_rel, Range, r_hat, Vc = compute_relative_kinematics(target, interceptor)

        #CHECK FOR DIRECT HIT
        if Range <= kill_radius:
            hit = True
            break

        #CHECK IF THE MISSILE IS NO LONGER CLOSING
        if Vc <= 0 and t > .1:
            break

        #LOS RATE
        los_rate = compute_los_rate(r_rel, v_rel, Range)

        #TARGET ACCELERATION
        mode = guidance_mode.upper()
        if mode == "PN":
            a_command = guidance.pn(r_hat, los_rate, Vc)
        elif mode == "APN":
            a_command = guidance.apn(r_hat, los_rate, Vc, target.a)
        elif mode == "ZEM":
            a_command = guidance.zem_guidance(r_rel, v_rel, target.a)
        else:
            while mode not in ["PN", "APN", "ZEM"]:
                mode = input("Enter a correct mode: ").upper()
        
        #AUTOPILOT CORRECTION
        a_actual = autopilot.update(a_command, dt)

        #LOGGING HISTORY
        accel_log.append([a_actual[0], a_actual[1], a_actual[2], np.sqrt(a_actual[0]**2 + a_actual[1]**2 + a_actual[2]**2)])
        range_log.append(Range)
        time_log.append(t)
        interceptor_pos_log.append(interceptor.r.copy())
        target_pos_log.append(target.r.copy())

        #INTERCEPTOR DYNAMICS
        interceptor.step_rk4(dt, a_actual)

        #TARGET DYNAMICS
        target.update(dt)

        #TIME STEP
        t += dt

    #FINAL MISS DISTANCE
    miss_distance = Range

    #CONVERT LIST TO NUMPY ARRAY FOR STATS
    if accel_log:
        accel_array = np.array(accel_log)
        avg_accel = float(np.mean(accel_array[:,3]))
        peak_accel = float(np.max(accel_array[:,3]))
    else:
        avg_accel = 0.0
        peak_accel = 0.0
                           

    #RETURN LIBRARY FULL OF DATA
    return{
        "model" : guidance_mode.upper(),
        "hit" : hit,
        "miss_distance" : miss_distance,
        "t_final" : t,
        "avg_accel" : avg_accel,
        "peak_accel" : peak_accel,
        "time_history" : np.array(time_log),
        "range_history" : np.array(range_log),
        "accel_history" : accel_array,
        "interceptor_history" : np.array(interceptor_pos_log),
        "target_history" : np.array(target_pos_log)
    }