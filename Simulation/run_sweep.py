#IMPORT LIBRARIES
import numpy as np
import time

#IMPORT CLASSES
from Simulation.monte_carlo import run_monte_carlo, summarize_monte_carlo

#SET UP THE VARIABLES
Sweep_variables = {
    #SEVERITY DICTIONARY TO PICK RANDOM VALUES
    "severity"  :   {
        "key"           :   "severity_mult",
        "baseline"      :   1.0,
        "default_min"   :   .5,
        "default_max"   :   3.0,
        "default_steps" :   6,
        "units"         :   "x baseline",
        "label"         :   "Target Maneuver Severity",
    },

    #N VALUE FOR NAVIGATION CONSTANT
    "N" :   {
        "key"   :   "N",
        "baseline"      :   3.0,
        "default_min"   :   2,
        "default_max"   :   6.0,
        "default_steps" :   5,
        "units"         :   "",
        "label"         :   "Navigation Constant N",
    },

    #POINTING ERROR DISTRIBUTION
    "pointing_error"    :   {
        "key"   :   "pointing_error_deg",
        "baseline"      :   20.0,
        "default_min"   :   0.0,
        "default_max"   :   40.0,
        "default_steps" :   5,
        "units"         :   "deg",
        "label"         :   "Pointing/Cueing Error",
    },

    #RANGE DISTRIBUTION
    "R_target"  :   {
        "key"   :   "R_target",
        "baseline"      :   None,
        "default_min"   :   500.0,
        "default_max"   :   3000.0,
        "default_steps" :   6,
        "units"         :   "m",
        "label"         :   "Engagement Range",
    },

    #STARTING VELOCITY
    "Vi"       :   {
        "key"           :   "Vi",
        "baseline"      :   None,
        "default_min"   :   150.0,
        "default_max"   :   400.0,
        "default_steps" :   5,
        "units"         :   "m/s",
        "label"         :   "Interceptor Closing Speed",
    }
}

#HALF WIDTH FOR GIVEN TRIAL COUNT
def wilson_ci_halfwidth(n,p=.5,z=1.96):
    #SAME FORMULA AS IN MONTE CARLO
    denom = 1+z**2/n
    margin = (z*np.sqrt((p*(1-p)/n) + (z**2/(4*n**2))))/denom
    return margin*100

#TRIALS FOR HALFWIDTH, FINDS SMALLEST N FOR VALUE UNDER GIVEN TARGET HALFWIDTH
def trials_for_halfwidth(target_halfwidth_pts, p = .5, z = 1.96, n_max = 20000):
    #MAKE SURE TARGET HALFWIDTH IS POTITIVE
    if target_halfwidth_pts <= 0:
        raise ValueError("target_halfwidth_pts must be positive")
    #ESTABLISH LOW AND HIGH
    lo, hi = 1, n_max
    if wilson_ci_halfwidth(n_max, p, z) > target_halfwidth_pts:
        #RETURN CEILING, REAL VALUE IS HIGHER SO CAP IT
        return n_max
    #ADJUST AND RUN LOOP FOR MID/LO VALUE
    while lo<hi:
        mid = (lo+hi)//2
        if wilson_ci_halfwidth(mid,p,z) <= target_halfwidth_pts:
            hi = mid
        else:
            lo = mid + 1
    return lo
    
#MENU FUNCTION FOR EITHER N OR HALFWIDTH
def resolve_trials_per_step(mode, value, p_assumed = .5):
    #HALFWIDTH GIVEN N
    if mode == "n":
        n = int(value)
        achieved = wilson_ci_halfwidth(n, p = p_assumed)
        print(f"  -> {n} trials/step gives a Wilson CI half-width of ±{achieved:.1f}pts "
            f"at p={p_assumed:.2f} (worst-case width; tighter near 0%/100% hit rate)")
        return n

    #N GIVEN HALFWIDTH
    elif mode == "halfwidth":
        n = trials_for_halfwidth(value, p = p_assumed)
        achieved = wilson_ci_halfwidth(n, p = p_assumed)
        print(f"  -> Target ±{value:.1f}pts at p={p_assumed:.2f} requires {n} trials/step "
              f"(achieves ±{achieved:.1f}pts)")
        return n
    else:
        raise ValueError(f"mode must be 'n' or 'halfwidth'. Entered mode is '{mode}")

#BUILD LIST OF FIXED LEVELS FOR ONE SWEEP VARIABLE
def build_sweep_levels(var_name, n_steps = None, level_min = None, level_max = None):
    #CHECK IF VARIABLE IS VALID
    if var_name not in Sweep_variables:
        raise ValueError(f"Unknown sweep variable '{var_name}'. Chose from: {list(Sweep_variables.keys())}")
    #GRAB VALUES
    spec = Sweep_variables[var_name]
    #RETURN IN LIST FORMAT
    lo = spec["default_min"] if level_min is None else level_min
    hi = spec["default_max"] if level_max is None else level_max
    steps = spec["default_steps"] if n_steps is None else n_steps
    return np.linspace(lo,hi,steps).tolist()

#RUN FULL SWEEP FOR ONE VARIABLE ON A SINGLE MONTE CARLO RUN
def run_sweep(var_name, levels = None, trials_per_step = 75, modes = None, master_seed = 0, verbose = True):
    #MAKE SURE NOTHING IS MISSING IF NOT INPUTTED
    if modes is None:
        modes = ["PN", "APN", "ZEM"]
    if levels is None:
        levels = build_sweep_levels(var_name)
    
    #GRAB OBJECT
    spec = Sweep_variables[var_name]
    key = spec["key"]

    #IF SHOWN THEN DISPLAY THE TABLE/VALUES
    if verbose:
        print(f"\n{'='*60}")
        print(f"SENSITIVITY SWEEP: {spec['label']}")
        print(f"Levels: {[f'{l:.2f}' for l in levels]} {spec['units']}")
        print(f"Trials/step: {trials_per_step}  |  Modes: {modes}  |  Total runs: {len(levels)*trials_per_step*len(modes)}")
        print(f"{'='*60}")
    
    #STORAGE
    sweep_results = {mode: [] for mode in modes}
    start_time = time.time()

    #TRIAL LOOP
    for level_idx, level in enumerate(levels):
        #SPECIAL SEED PER LEVEL
        level_seed = master_seed + level_idx
        #N IS SPECIAL CASE, SINCE IT'S NOT AN INITIAL CONDITION, BUT A GUIDANCE LAW PARAMATER
        if var_name == "N":
            mc_out = run_monte_carlo(n_trials = trials_per_step, modes = modes, master_seed = level_seed, N = level, N_zem = level, quiet = True)
        #ALL OTHER CASES
        else:
            mc_out = run_monte_carlo(n_trials = trials_per_step, modes = modes, master_seed = level_seed, ic_overrides = {key: level}, quiet = True)
        
        #NOW RUN MONTE CARLO
        level_summary = summarize_monte_carlo(mc_out)

        #STORE DATA
        for mode in modes:
            sweep_results[mode].append({
                "level" :   level,
                "hit_rate"  :   level_summary[mode]["hit_rate"],
                "ci_low"    :   level_summary[mode]["ci_low"],
                "ci_high"   :   level_summary[mode]["ci_high"],
                "miss_median"   :   level_summary[mode]["miss_median"],
                "saturation_mean"   :   level_summary[mode]["saturation_mean"],
                "tti_mean"  :   level_summary[mode]["tti_mean"]
            })

        #SHOW DATA IF WANTED
        if verbose:
            #LINE THAT'S GONNA BE USED
            line = f"   level={level:>8.2f} {spec['units']:<10}"
            #LOOP
            for mode in modes:
                hr = sweep_results[mode][-1]["hit_rate"]
                line += f"  {mode}:{hr:5.1f}%"
            print(line)
        
    #TIME TAKEN
    elapsed = time.time() - start_time
    #DISPLAY IF WANTED
    if verbose:
        print(f"{'-'*60}")
        print(f"Sweep complete. {elapsed: .1f}s total.\n")
    
    #RETURN DATA
    return {
        "var_name": var_name,
        "spec": spec,
        "levels": levels,
        "trials_per_step": trials_per_step,
        "modes": modes,
        "master_seed": master_seed,
        "sweep_results": sweep_results,
    }
    