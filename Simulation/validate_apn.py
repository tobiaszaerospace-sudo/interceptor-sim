#VALIDATE AUGMENTED PROPORTIONAL NAVIGATION

#IMPORT STUFF
import numpy as np
from scipy.stats import linregress
from Config.settings import settings
from Simulation.simulate import run_simulator

#NAVIGATIONS CONSTANT
N_values = [2,3,4,5]

#ENGAGEMENT PARAMETERS
R0 = 1000.0
Vi = 300.0
Vt = 100.0
Epsilon_deg = 5.0
Epsilon_rad = np.radians(Epsilon_deg)

#CONSTANT TARGET, INITIALLY TRANSVERSE TO LOS
target_accel = np.array([0.0, 3.0, 0.0])

#VALIDATION INITIAL CONDITIONS
def build_validation_ic():
    rt0 = [R0, 0.0, 0.0]
    vt0 = [Vt, 0.0, 0.0]
    ri0 = [0.0, 0.0, 0.0]
    vi0 = [
        Vi*np.cos(Epsilon_rad),
        Vi*np.sin(Epsilon_rad),
        0.0
    ]

    return{
        "ri0" : ri0,
        "vi0" : vi0,
        "target_data" : {
            "initial_position" : rt0,
            "initial_velocity" : vt0,
            "motion_model" : "constant_acceleration",
            "params" : {"accel" : target_accel.tolist()}
        }
    }

    #GET ZEM FROM HISTORY
def compute_apn_zem_from_history(history):
        t_gos = []
        zems = []
        times = []

        #CYCLE THROUGH
        for step in history:
            closing_velocity = step['closing_velocity']
            range_to_target = step['range']

            #SKIP INITIAL STEP AND SAMPLES WITHOUT USEFUL TTG
            if step['t'] <= 0.0 or closing_velocity < 1.0 or range_to_target < 1e-9:
                continue

            #CALCULATIONS
            t_go = range_to_target / closing_velocity
            r_rel = np.asarray(step["r_rel"], dtype=float)
            v_rel = np.asarray(step["v_rel"], dtype=float)

            zem_vec = r_rel + v_rel * t_go + 0.5 * target_accel * (t_go**2)
            r_hat = r_rel / range_to_target
            zem_perp = zem_vec - np.dot(zem_vec, r_hat) * r_hat
            zem_mag = float(np.linalg.norm(zem_perp))

            #ZEM MAGNITUDE CHECK
            if zem_mag < 1e-9:
                continue

            #STORE VALUES
            t_gos.append(t_go)
            zems.append(zem_mag)
            times.append(step['t'])

        #RETURN VALUES
        return np.asarray(t_gos), np.asarray(zems), np.asarray(times)

    #CHECKING ZEM DECAY SLOPE
def fit_apn_zem_decay_slope(t_gos, zems, times):
        #CHECK FOR LOW NUMBER OF DATA POINTS
        if len(t_gos) < 5:
            return np.nan, np.nan, np.nan

        #EXCLUDE TERMINAL REGIONS 
        mask = (t_gos > .3) & (times > 0.0)
        if mask.sum() < 5:
            return np.nan, np.nan, np.nan

        #STATISTICAL ANALYSIS FIT
        slope, intercept, r_value, p_value, std_err = linregress(
        np.log(t_gos[mask]),
        np.log(zems[mask]),
        )
        return slope, r_value**2, std_err

    #VALIDATION
def run_validation():
        ic = build_validation_ic()
        previous_guidance_mode = settings.guidance_mode
        previous_use_ekf = settings.use_ekf
        settings.guidance_mode = "APN"
        settings.use_ekf = False

        #SETUP RESULTS
        results = []

        #SAME FORMAT AS PN VALIDATION
        print("\n" + "=" * 78)
        print("APN GUIDANCE ANALYTICAL VALIDATION")
        print(
            f"Engagement: R0={R0}m  Vi={Vi}m/s  Vt={Vt}m/s  "
            f"epsilon={Epsilon_deg}deg"
        )
        print(f"Target acceleration: {target_accel.tolist()} m/s^2")
        print("Theory: corrected ZEM(t_go) scales approximately as t_go^N")
        print(
            f"Note: first-order autopilot lag (tau={settings.tau}s), RK4 "
            "integration, and t_go=range/Vc cause deviations from the ideal slope."
        )
        print("=" * 78)
        print(
            f"{'N':>5}  {'Measured Slope':>15}  {'Theoretical':>12}  "
            f"{'Deviation':>10}  {'R^2':>7}  {'Hit':>5}"
        )
        print("-" * 78)

        #NORMAL OUTCOME
        try:
            #CYCLE THROUGH VALUES
            for N in N_values:
                #GET RESULT
                out = run_simulator(settings, ic_override = ic, save_history = True, N = N, N_zem = N)
                t_gos, zems, times = compute_apn_zem_from_history(out['history'])

                #CHECK FOR SMALL RUNS
                if len(t_gos) < 5:
                    measured_slope, r_squared, std_err = np.nan, np.nan, np.nan
                else:
                    measured_slope, r_squared, std_err = fit_apn_zem_decay_slope(t_gos, zems, times)

                #CHECK THE SLOPE
                if np.isnan(measured_slope):
                    deviation_pct = np.nan
                    print(f"{N:>5.1f}  {'INSUFFICIENT DATA':>15}  {N:>12.4f}  "
                    f"{'N/A':>10}  {'N/A':>7}  {str(out['hit']):>5}")
                else:
                    deviation_pct = abs(measured_slope-N)/N*100
                    print(f"{N:>5.1f}  {measured_slope:>15.4f}  {N:>12.4f}  "
                    f"{deviation_pct:>9.1f}%  {r_squared:>7.4f}  "
                    f"{str(out['hit']):>5}")

                #APPEND RESULTS
                results.append({
                    "N": N,
                    "measured_slope": measured_slope,
                    "r_squared": r_squared,
                    "std_err": std_err,
                    "deviation_pct": deviation_pct,
                    "t_gos": t_gos,
                    "zems": zems,
                    "hit": out["hit"],
                    "miss_distance": out["miss_distance"]
                    }
                    )

        finally:
            settings.guidance_mode = previous_guidance_mode
            settings.use_ekf = previous_use_ekf

        #DATA ANALYSIS/MEANING SECTION
        print("=" * 78)
        print("Interpretation:")
        print("  Deviation < 5%   -> close to the ideal analytical slope")
        print("  Deviation 5-15%  -> lag/nonlinear effects may explain the difference")
        print("  Deviation > 15%  -> inspect the APN law and selected fit interval")
        print(
            "This validates APN behavior against its corrected-ZEM decay relation; "
            "it does not validate the rest of the simulation system.\n")

        #RETURN EVERYTHING
        return results, ic
                    
            