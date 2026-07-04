#ANALYTICAL VALIDATION OF PN GUIDANCE WITH ZEM DECAY LAW
#DERIVED FROM FOLLOWING SOURCES
# LINEARIZED PN ZEM DECAY LAWS DERIVED FROM WORK IN JULY
# ZARCHAN "TACTIAL AND STRATEGIC MISSILE GUIDANCE" AIAA 2012

#GRAB LIBRARIES AND FILES
import numpy as np
from scipy.stats import linregress
from Config.settings import settings
from Simulation.simulate import run_simulator

#N VALUES TO VALIDATE ACROSS
N_values = [2.0,3.0,4.0,5.0]

#ENGAGEMENT PARAMATERS - CAN BE FIXED FOR PURPOSES OF THIS, NO USER SELECTION
R0 = 1000.0 #INITIAL RANGE
Vi = 300.0 #INITIAL INTERCEPTOR SPEED
Vt = 100.0 # TARGET SPEED 
Epsilon_deg = 5.0 #POINTING ERROR OFF LOS, SMALL FOR LINEARIZATION
Epsilon_rad = np.radians(Epsilon_deg) #CONVERT TO RADIANS

#BUILD FIXED IC DICTIONARY FOR TARGET(AT RANGE R0 ON X AXIS) AND INTERCEPTOR(AT ORIGIN POINTING AT TARGET WITH ANGLE ERROR)
def build_validation_ic():
    #TARGET POSITION AND VELOCITY
    rt0 = [R0, 0.0, 0.0]
    vt0 = [Vt, 0.0, 0.0]
    
    #INTERCEPTOR POSITION AND VELOCITY
    ri0 = [0.0, 0.0, 0.0]
    vi0 = [Vi*np.cos(Epsilon_rad),
           Vi*np.sin(Epsilon_rad),
           0.0]
    
    #RETURN IC VALUES
    return {
        "ri0": ri0,
        "vi0": vi0,
        "target_data" : {
            "initial_position": rt0,
            "initial_velocity": vt0,
            "motion_model" : "constant_velocity",
            "params" : {}
        }
    }

#COMPUTE ZEM DECAY LAW
def compute_zem_from_history(history):
    #ESTABLISH EMPTY LISTS
    t_gos = []
    zems = []

    #LOOP THROUGH HISTORY
    for step in history:
        #GRAB VC AND RANGE
        Vc = step["closing_velocity"]
        Range = step['range']

        #SKIP STEP WHERE CLOSING VELOCITY IS NEAR ZERO OR NEGATIVE
        if Vc < 1.0:
            continue

        t_go = Range/Vc
        r_rel = np.array(step["r_rel"])
        v_rel = np.array(step["v_rel"])
        zem_vec = r_rel + v_rel * t_go
        zem_mag = np.linalg.norm(zem_vec)

        #SKIP SMALL ZEM VALUES, AVOID LOG OF ZERO ERRORS
        if zem_mag < 1e-3:
            continue
        
        #LOG DATA
        t_gos.append(t_go)
        zems.append(zem_mag)
    
    #RETURN FULL LISTS AT FINISH AS ARRAYS
    return np.array(t_gos), np.array(zems)

#FIND ZEM DECAY SLOPE 
def fit_zem_decay_slope(t_gos, zems):
    #ONLY USE EARLY-MID ENGAGEMENT WHERE LINEARIZATION IS VALID, AUTOPILOT LAG HASN'T CAUSED LARGE DEVIATIONS, ARE ENOUGH POINTS FOR RELIABLE REGRESSION
    mask = t_gos > .3
    if mask.sum() < 5:
        #NOT ENOUGH POINTS, ENGAGEMENT TOO SHORT OR ZEM IS NULLED TOO QUICKLY
        return np.nan, np.nan, np.nan

    #LINEAR REGRESSION MATH AND LOG VALUES CALCULATION
    log_tgo  = np.log(t_gos[mask])
    log_zem  = np.log(zems[mask])
    slope, intercept, r_value, p_value, std_err = linregress(log_tgo, log_zem)
    return slope, r_value**2, std_err

#VALIDATE PN GUIDANCE, MAIN LOOP HERE
def run_validation():
    #LOOP ONCE PER N VALUE, SAME IC EVERY TIME
    ic = build_validation_ic()
    settings.guidance_mode = "PN"

    #SETUP RESULTS STORAGE
    results = []

    #PRINT OUT MENU
    print("\n" + "="*65)
    print("PN GUIDANCE ANALYTICAL VALIDATION")
    print(f"Engagement: R0={R0}m  Vi={Vi}m/s  Vt={Vt}m/s  epsilon={Epsilon_deg}deg")
    print(f"Theory: ZEM(t_go) = ZEM0 * (t_go/t_go0)^N  ->  log-log slope = N")
    print(f"Note: first-order autopilot lag (tau={settings.tau}s) expected to cause\nsmall deviation from ideal slope, especially near interception")
    print("="*65)
    print(f"{'N':>5}  {'Measured Slope':>15}  {'Theoretical':>12}  {'Deviation':>10}  {'R²':>6}  {'Hit':>5}")
    print("-"*65)

    #LOOP THROUGH N VALUES
    for N in N_values:
        #RUN REAL SIMULATOR WITH N VALUE
        out = run_simulator(settings, ic_override = ic, save_history = True, N = N, N_zem = N)
        history = out["history"]

        #GRAB ZEM TIME SERIES FROM HISTORY
        t_gos, zems = compute_zem_from_history(history)

        #IN EVENT OF INSUFFICIENT DATA POINTS
        if len(t_gos) < 5:
            print(f"{N:>5.1f}  {'INSUFFICIENT DATA':>15}  {N:>12.4f}  {'N/A':>10}  {'N/A':>6}  {str(out['hit']):>5}")
            results.append({
                "N": N,
                "measured_slope": np.nan,
                "r_squared": np.nan,
                "t_gos": t_gos,
                "zems" : zems,
                "hit": out['hit']
            })
            continue

        #FIT LOG LOG SLOPE
        measured_slope, r_squared, std_err = fit_zem_decay_slope(t_gos, zems)

        #COMPUTE PERCENT DEVIATION FROM PERFECT THEORETICAL SLOPE
        deviation_pct = abs(measured_slope - N) / N * 100 if not np.isnan(measured_slope) else np.nan

        #PRINT RESULTS
        print(f"{N:>5.1f}  {measured_slope:>15.4f}  {N:>12.4f}  {deviation_pct:>9.1f}%  {r_squared:>6.4f}  {str(out['hit']):>5}")

        #APPEND RESULTS TO LIST
        results.append({
            "N" : N,
            "measured_slope" : measured_slope,
            "r_squared" : r_squared,
            "std_err" : std_err,
            "t_gos" : t_gos,
            "zems" : zems,
            "hit" : out['hit']
        })

    #WHAT RESULTS MEAN SUMMARY
    print("="*65)
    print("Deviation < 5%  -> sim consistent with theory")
    print("Deviation 5-15% -> small lag/nonlinear effects, expected and acceptable")
    print("Deviation > 15% -> investigate, potential guidance or kinematics bug\n")
 
    return results, ic