#IMPORT LIBRARY
import numpy as np
#IMPORT ALL OTHER FILES
from Simulation.initial_conditions import InitialConditions
from Simulation.target import Target
from Simulation.interceptor import Interceptor
from Simulation.autopilot import Autopilot
from Simulation.guidance_palumbo import Guidance
from Simulation.relative_kinematics import compute_relative_kinematics
from Simulation.los_rate import compute_los_rate
from Config.settings import settings

#SIMULATION FUNCTION
def run_simulator(settings, ic_override = None, save_history = True, N = None, N_zem = None):
    #RUNS A SINGLE SIMULATION WITH GUIDANCE LAW, WILL RETURN DICTIONARY
    #INITIALIZE SIMULATION PARAMETERS
    dt = settings.dt
    t_max = settings.t_max
    kill_radius = settings.kill_radius
    max_accel = settings.max_accel
    tau = settings.tau
    #CHANGED N AND N_ZEM FOR SECONDARY MONTE CARLO ABILITY
    N = settings.N if None else N
    N_zem = settings.N_zem if N_zem is None else N_zem

    #INITIAL CONDITIONS
    #CHECK FOR MULTIPLE SIMULATION PLOT
    if ic_override is not None:
        ri0 = ic_override["ri0"]
        vi0 = ic_override["vi0"]
        target_data = ic_override["target_data"]
    else:
        ic = InitialConditions()
        ri0, vi0 = ic.build_interceptor()
        target_data = ic.build_target()
    mode = settings.guidance_mode.upper()
    while mode not in ["PN", "APN", "ZEM"]:
        mode = input("Enter a correct mode: ").upper()

    #OBJECTS
    target = Target(target_data["initial_position"], target_data["initial_velocity"], target_data["motion_model"], target_data["params"])
    interceptor = Interceptor(ri0, vi0)
    guidance = Guidance(N=N, N_zem = N_zem)
    autopilot = Autopilot(max_accel = max_accel, tau = tau)

    #DIVERGENCE CHECK
    div_count = settings.div_count
    div_counter = 0

    #LOGGING
    t = 0.0
    hit = False
    history = []

    #INITIALIZE MISS DISTANCE
    min_range = float(1e99)
    min_range_time = 0.0

    #INITIALIZE SATURATION COUNTER
    saturated_steps = 0
    total_steps = 0
    accel_sum = 0.0
    peak_accel_running = 0.0

    #START LOOP
    while t < t_max:

        #RELATIVE KINEMATICS
        r_rel, v_rel, Range, r_hat, Vc = compute_relative_kinematics(target, interceptor)

        #UPDATE MINIMUM RANGE
        if Range < min_range:
            min_range = Range
            min_range_time = t

        #CHECK FOR DIRECT HIT
        if Range <= kill_radius:
            hit = True
            break

        #CHECK IF THE MISSILE IS NO LONGER CLOSING
        if Vc < 0:
            div_counter += 1
            if div_counter >= div_count:
                if settings.debug:
                    print("Divergence detected, ending simulation.")
                break
        else:
            div_counter = 0

        #LOS RATE
        los_rate = compute_los_rate(r_rel, v_rel, Range)

        #LOGGING STATE AND RUNNING CALCULATION
        if mode == "PN":
            a_command = guidance.pn(r_hat, Vc, los_rate)
        elif mode == "APN":
            a_command = guidance.apn(r_hat, Vc, los_rate, target.a)
        elif mode == "ZEM":
            a_command = guidance.zem_guidance(r_rel, v_rel, target.a, Vc, Range)
        
        #AUTOPILOT CORRECTION
        a_actual = autopilot.update(a_command, dt)
        interceptor.set_acceleration(a_actual)

        #TRACK SATURATION
        accel_mag_actual = np.sqrt(a_actual[0]**2+a_actual[1]**2+a_actual[2]**2)
        total_steps += 1
        if accel_mag_actual >= max_accel*.99:
            saturated_steps += 1
        
        #ACCEL ACCUMULATION FOR INDEPENDENCE OF SAVE HISTORY
        accel_sum += accel_mag_actual
        if accel_mag_actual > peak_accel_running:
            peak_accel_running = accel_mag_actual

        if settings.debug:
            print(
                f"t={t:.2f}, "
                f"a_cmd={a_command}, "
                f"a_actual={a_actual}, "
                f"|a|={np.linalg.norm(a_actual):.3f}, "
                f"v={interceptor.v}")

        #LOGGING HISTORY
        step = {
            "t": t,
            "interceptor_pos" : interceptor.r.copy(),
            "interceptor_vel" : interceptor.v.copy(),
            "target_pos" : target.r.copy(),
            "target_vel" : target.v.copy(),
            "r_rel" : r_rel.copy(),
            "v_rel" : v_rel.copy(),
            "range" : Range,
            "closing_velocity" : Vc,
            "los_rate" : los_rate,
            "los_angle" : np.arctan2(r_rel[1], r_rel[0]),
            "a_command" : a_command.copy(),
            "a_actual" : a_actual.copy(),
            "accel_mag" : np.sqrt(a_actual[0]**2 + a_actual[1]**2 + a_actual[2]**2),
        }
        if save_history:
            history.append(step)

        #INTERCEPTOR DYNAMICS
        interceptor.step_rk4(dt, a_actual)

        #TARGET DYNAMICS
        target.update(dt)

        #TIME STEP
        t += dt

    #FINAL MISS DISTANCE
    miss_distance = Range  

    #ACCELERATION STATS
    if history:
        accel_mags = [step["accel_mag"] for step in history]
        avg_accel = float(np.mean(accel_mags))
        peak_accel = float(np.max(accel_mags))
    else:
        avg_accel = accel_sum / total_steps if total_steps else 0.0
        peak_accel = peak_accel_running

    #SATURATION FRACTION
    saturation_fraction = saturated_steps / total_steps if total_steps else 0.0                  

    #TERMINATION REASONING
    if hit:
        termination_reason = "hit"
    elif div_counter >= div_count:
        termination_reason = "diverged"
    elif Vc > 0:
        termination_reason = "timeout_closing"
    else:
        termination_reason = "timeout_receding"

    #RETURN LIBRARY FULL OF DATA
    return {
        "model" : mode,
        "hit" : hit,
        "miss_distance" : min_range,
        "t_final" : t,
        "avg_accel" : avg_accel,
        "peak_accel" : peak_accel,
        "saturation_fraction" : saturation_fraction,
        "termination_reason" : termination_reason,
        "N"     :   N,
        "N_zem" :   N_zem,
        "history" : history,
    }