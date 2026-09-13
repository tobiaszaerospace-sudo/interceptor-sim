#IMPORT LIBRARY
import numpy as np
import math
import time
#IMPORT ALL OTHER FILES
from Simulation.initial_conditions import InitialConditions
from Simulation.target import Target
from Simulation.interceptor import Interceptor
from Simulation.autopilot import Autopilot
from Simulation.guidance_palumbo import Guidance
from Simulation.relative_kinematics import compute_relative_kinematics
from Simulation.los_rate import compute_los_rate
from Config.settings import settings
from Simulation.sensor_noise import SensorNoise
from Simulation.ekf import EKF

#SIMULATION FUNCTION
def run_simulator(settings, ic_override = None, save_history = True, N = None, N_zem = None, move_gimbal = False, gimbal_port = None, gimbal_buad = None, gimbal_rate_hz = 20, noise_seed = None):
    #RUNS A SINGLE SIMULATION WITH GUIDANCE LAW, WILL RETURN DICTIONARY
    #INITIALIZE SIMULATION PARAMETERS
    dt = settings.dt
    t_max = settings.t_max
    kill_radius = settings.kill_radius
    max_accel = settings.max_accel
    tau = settings.tau
    #CHANGED N AND N_ZEM FOR SECONDARY MONTE CARLO ABILITY
    N = settings.N if N is None else N
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

    #NEES ACCUMULATOR FOR EKF
    nees_sum = 0.0
    nees_count = 0
    last_nees = None

    #INITIALIZE SATURATION COUNTER
    saturated_steps = 0
    total_steps = 0
    accel_sum = 0.0
    peak_accel_running = 0.0

    #CHECK GIMBAL AND IMU PHYSICAL SERIAL PORT
    shared_ser = None
    resolved_gimbal_port = gimbal_port or settings.servo_port
    resolved_gimbal_baud = gimbal_buad or settings.servo_baud
    ports_shared = (move_gimbal and settings.use_ekf and settings.use_imu and resolved_gimbal_port == settings.imu_port)

    #IF THE PORTS ARE SHARED OPEN ONE CONNECTION FOR BOTH
    if ports_shared:
        try:
            import serial as _serial
            shared_ser = _serial.Serial(resolved_gimbal_port, resolved_gimbal_baud, timeout = .05)
            time.sleep(2)
            print(f"Shared gimbal/IMU serial connected on {resolved_gimbal_port}")
        except Exception as e:
            print(f"Shared serial connection failed: {e}. Continueing without hardware.")
            shared_ser = None
            move_gimbal = False
            settings.use_imu = False
    
    #EKF AND SENSOR NOISE SETUP
    if settings.use_ekf:
        sensor = SensorNoise(settings, rng_seed = noise_seed, shared_ser = shared_ser)
        ekf = EKF(dt = dt)
    else:
        sensor = None
        ekf = None

    #GIMBAL HARDWARE SETUP
    servo = None
    if move_gimbal:
        try:
            from Hardware.servo import ServoController
            servo = ServoController(resolved_gimbal_port, resolved_gimbal_baud, ser = shared_ser)
        except Exception as e:
            print(f"Gimbal connection failed: {e}. Continuing wihtout hardware")
            servo = None

    #CALCULATE SIM STEPS FOR GIMBAL SERIAL WRITES, CAN'T KEEP UP WITH DT
    gimbal_send_interval = max(1, int(round(1/(gimbal_rate_hz*dt))))
    step_index = 0

    #FIXED WALL-CLOCK REFERENCE FOR REAL TIME PACING
    gimbal_requested = servo is not None
    sim_start_wall = time.time() if gimbal_requested else None

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

        #IF EKF IS ENABLED, USE NOISY ESTIMATE
        if settings.use_ekf:
            meas = sensor.measure(r_rel)
            ekf.predict()
            ekf.update(meas["az_meas"], meas['el_meas'])
            r_rel_g = ekf.r_est()
            v_rel_g    = ekf.v_est()
            Range_g    = ekf.range_est()
            r_hat_g    = ekf.range_hat_est()
            Vc_g       = ekf.Vc_est()
            los_rate_g = compute_los_rate(r_rel_g, v_rel_g, Range_g)
            nees       = ekf.nees(r_rel, v_rel)
            nees_sum += nees
            nees_count += 1
            last_nees = nees
        else:
            r_rel_g, v_rel_g, Range_g, r_hat_g, Vc_g, los_rate_g = r_rel, v_rel, Range, r_hat, Vc, los_rate
            nees = None
            
        #LOGGING STATE AND RUNNING CALCULATION
        if mode == "PN":
            a_command = guidance.pn(r_hat_g, Vc_g, los_rate_g)
        elif mode == "APN":
            a_command = guidance.apn(r_hat_g, Vc_g, los_rate_g, target.a)
        elif mode == "ZEM":
            a_command = guidance.zem_guidance(r_rel_g, v_rel_g, target.a, Vc_g, Range_g)
        
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
            "target_accel" : target.a.copy(),
            "r_rel" : r_rel.copy(),
            "v_rel" : v_rel.copy(),
            "range" : Range,
            "closing_velocity" : Vc,
            "los_rate" : los_rate,
            "los_angle" : np.arctan2(r_rel[1], r_rel[0]),
            "a_command" : a_command.copy(),
            "a_actual" : a_actual.copy(),
            "accel_mag" : np.sqrt(a_actual[0]**2 + a_actual[1]**2 + a_actual[2]**2),
            "r_est" :   r_rel_g.copy() if settings.use_ekf else None,
            "v_est" :   v_rel_g.copy() if settings.use_ekf else None,
            "range_est" : Range_g if settings.use_ekf else None,
            "nees" : nees,
        }
        if save_history:
            history.append(step)

        #GIMBAL LIVE MOVEMENT
        if gimbal_requested and step_index % gimbal_send_interval == 0:
            if servo is not None:
                v = interceptor.v
                speed = np.linalg.norm(v)
                az_deg = math.degrees(math.atan2(v[1], v[0]))
                el_deg = math.degrees(math.asin(float(np.clip(v[2]/speed, -1.0, 1.0)))) if speed > 0 else 0.0
                try:
                    servo.set_servo_angle(az_deg, el_deg)
                except Exception as e:
                    print(f"Gimbal write failed: {e}. Disabling gimbal hardware for the rest of this run")
                    servo = None
                target_wall = sim_start_wall + t
                now = time.time()
                if target_wall > now:
                    time.sleep(target_wall-now)   

        step_index += 1


        #INTERCEPTOR DYNAMICS
        interceptor.step_rk4(dt, a_actual)

        #TARGET DYNAMICS
        target.update(dt)

        #TIME STEP
        t += dt
    
    #CLEAN UP HARDWARE CONNECTIONS
    if sensor is not None:
        sensor.close()
    if servo is not None:
        servo.close()
    if shared_ser is not None and shared_ser.is_open:
        shared_ser.close()

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

    #NEES SUMMARY
    mean_nees = (nees_sum/nees_count) if nees_count > 0 else None
    final_nees = last_nees
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
        "mean_nees" : mean_nees,
        "final_nees" : final_nees,
        "history" : history,
    }