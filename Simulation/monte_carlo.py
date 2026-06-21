#IMPORT LIBRARIES
import numpy as np
import time
#IMPORT CLASSES
from Config.settings import settings
from Simulation.simulate import run_simulator
from Simulation.initial_conditions import InitialConditions


#WILSON SCORE CONFIDENCE INTERVAL FOR EXTREME HIT RATES(0/100%)
#z=1.96 FOR 95% CONFIDENCE INTERVAL
def wilson_ci(hits, n, z=1.96):
    #STOP DIV BY 0 IF NO TRIALS WERE RUN
    if n == 0:
        return(0.0,0.0)
    #SAMPLE PROPORTION AS FRACTION
    p = hits/n

    #WILSON SCORE PARTS
    denom = 1 + z**2/n
    center = (p+z**2/(2*n))/denom
    margin = (z*np.sqrt((p*(1-p)/n) + (z**2/(4*n**2))))/denom

    #KEEP BETWEEN 0 AND 1, PROPORTIONS CAN'T EXCEED BOUNDS
    return(max(0.0,center-margin), min(1.0,center+margin))


#MONTE CARLO RUNNER
def run_monte_carlo(n_trials = 500, modes = None, master_seed = 0, convergence_checkpoints = 10):
    #CHECK FOR IF MODES GOT PASSED THROUGH
    if modes is None:
        modes = ["PN", "APN", "ZEM"]
    
    rng = np.random.default_rng(master_seed)

    #GENERATE ALL ICs FIRST SO EVERY GUIDANCE LAW HAS SAME ENGAGEMENT
    ics = [InitialConditions.build_random_ic(rng) for _ in range(n_trials)]

    #CONVERGENCE CHECKPOINT COMPUTATION
    checkpoint_indeces = set(int(idx) for idx in np.linspace(0,n_trials-1,convergence_checkpoints))

    #SAVING SMALL SET OF TRIALS FOR TRAJECTORY/ZEM PLOTS LATER FOR COMPARISON, ALL OF THEM WOULD BE TOO MUCH
    n_samples = min(5,n_trials)
    sample_indeces = set(int(idx) for idx in np.linspace(0,n_trials-1,n_samples))

    #STORE FOR DIFFERENT MODES
    results = {mode: [] for mode in modes}
    sample_trajectories = {mode: {} for mode in modes}
    convergence = {mode: [] for mode in modes}

    #FORMAT THE TABLE
    print(f"\n=== Monte Carlo Analysis ===")
    print(f"Trials:{n_trials}   |   Modes: {modes}  |   Seed: {master_seed}")
    print("-"*60)

    #RUN THROUGH LOOPS FOR SIMULATIONS
    for mode in modes:
        settings.guidance_mode = mode
        print(f"Running {mode}...", end="", flush=True)

        #TIMER FOR MODE'S TRIAL LOOP
        start_time = time.time()

        #RUNNING HIT COUNT FOR CONVERGENCE TRACKING
        running_hits = 0

        #STORE INDEX AND VALUE THROUGH LOOP
        for i, ic in enumerate(ics):
            #ONLY SAVE FULL HISTORY FOR SAMPLED TRIAL INDECES
            save_hist = i in sample_indeces

            #FOR REGULAR RUNS
            try:
                #RUN ENGAGEMENT 
                out = run_simulator(settings, ic_override = ic, save_history = save_hist)
                trial = {
                    "trial"         :   i,
                    "mode"          :   mode,
                    "motion_type"   :   ic["target_data"]["motion_model"],
                    "hit"           :   out["hit"],
                    "miss_distance" :   out['miss_distance'],
                    "peak_accel"    :   out["peak_accel"],
                    "avg_accel"     :   out["avg_accel"],
                    "t_final"       :   out["t_final"],
                    "saturation_fraction"   :   out['saturation_fraction'],
                    "termination_reason"    :   out["termination_reason"]
                }

                #STORE FULL HISTORY FOR SAMPLE TRIALS
                if save_hist:
                    sample_trajectories[mode][i] = out["history"]
            #CATCH ERRORS SO ENTIRE MONTE CARLO DOESN'T CRASH
            except Exception as e:
                trial = {
                    "trial"         :   i,
                    "mode"          :   mode,
                    "motion_type"   :   ic["target_data"]["motion_model"],
                    "hit"           :   False,
                    "miss_distance" :   np.nan,
                    "peak_accel"    :   0.0,
                    "avg_accel"     :   0.0,
                    "t_final"       :   0.0,
                    "saturation_fraction"   :   0.0,
                    "termination_reason"   :   "error",
                    "error"         :   str(e)
                }
            
            #NOW STORE THE RESULT
            results[mode].append(trial)

            #UPDATE HIT COUNT
            if trial['hit']:
                running_hits += 1

            #RECORD CONVERGENCE SAMPLE EVERY CONVERGENCE INTERVAL TRIAL
            if i in checkpoint_indeces or (i+1) == n_trials:
                convergence[mode].append({
                    "n" :   i+1,
                    "hit_rate"  :   running_hits/(i+1)*100
                })
            
        #ELAPSED TIME FOR INDIVIDUAL MODE'S FULL TRIAL SET
        elapsed = time.time()-start_time
        
        #SUMMARIZE FOR EACH MODE(T STANDS FOR TRIAL)
        hits = sum(t["hit"] for t in results[mode])
        hit_rate = hits/n_trials*100
        misses = [t["miss_distance"] for t in results[mode] if not t["hit"] and not np.isnan(t["miss_distance"])]
        med_miss = np.median(misses) if misses else np.nan
        #DISPLAY IMMEDIATE HIT RATE AND MED MISS RESULTS
        print(f"Done. Hit rate: {hit_rate:.1f}%     |    Median miss: {med_miss:.2f}m")
    
    #FORMAT STUFF
    print("-"*60)
    print("Monte Carlo complete.\n")
    return {
        "results"   :   results,
        "convergence"   :   convergence,
        "sample_trajectories"   :   sample_trajectories,
        "n_trials"  :   n_trials,
        "modes"     :   modes,
        "master_seed"   :   master_seed,
    }

#FULL SUMMARY STATISTIC OUTPUTS
def summarize_monte_carlo(mc_output):
    #UNPACK MONTE CARLO OUTPUT
    results = mc_output['results']
    convergence = mc_output['convergence']
    n_trials = mc_output['n_trials']
    modes = mc_output['modes']

    #START SUMMARY LIBRARY
    summary = {}

    #OPEN UP RESULTS AND STORE
    for mode in modes:

        #GRAB ALL TRIALS
        trials = results[mode]
        n = len(trials)

        #COUNT HITS
        hits = sum(t["hit"] for t in trials)
        hit_rate = hits/n*100

        #95% CONFIDENCE INTERVAL ON TRUE INTERCEPT PROBABILITY
        ci_low, ci_high = wilson_ci(hits,n)

        #MISS DISTANCE STATISTICS FOR NON HIT TRIALS
        misses = [t["miss_distance"] for t in trials
                  if not t['hit'] and not np.isnan(t['miss_distance'])]
        miss_mean = np.mean(misses) if misses else np.nan
        miss_std = np.std(misses) if misses else np.nan
        miss_med = np.median(misses) if misses else np.nan
        miss_95 = np.percentile(misses,95) if misses else np.nan

        #MISS DISTANCE STATISTICS FOR ALL TRIALS INCLUDING HITS
        all_miss = [t["miss_distance"] for t in trials if not np.isnan(t['miss_distance'])]
        all_miss_mean = np.mean(all_miss) if all_miss else np.nan
        all_miss_std = np.std(all_miss) if all_miss else np.nan

        #ACCELERATION STATISTICS
        peak_med = np.median([t['peak_accel'] for t in trials])
        avg_med = np.median([t['avg_accel'] for t in trials])

        #SATURATION STATISTICS
        sat_fracs = [t['saturation_fraction'] for t in trials if t['hit']]
        sat_mean = np.mean(sat_fracs)
        sat_med = np.median(sat_fracs)

        #TIME TO INTERCEPT FOR HITS ONLY 
        t_hits = [t["t_final"] for t in trials if t['hit']]
        tti_mean = np.mean(t_hits) if t_hits else np.nan
        tti_std = np.std(t_hits) if t_hits else np.nan

        #TERMINATION REASONING
        term_counts = {}
        for t in trials:
            reason = t['termination_reason']
            term_counts[reason] = term_counts.get(reason,0)+1
        
        #MOTION BREAKDOWN
        motion_breakdown = {}
        for mt in ['constant_velocity','constant_acceleration','weaving']:
            mt_trials = [t for t in trials if t['motion_type'] == mt]
            if mt_trials:
                mt_hit_rate = sum(t['hit'] for t in mt_trials)/len(mt_trials) * 100
                motion_breakdown[mt] = {'n': len(mt_trials),
                                        'hit_rate': mt_hit_rate}

        summary[mode] = {
            "n"             : n,
            "hit_rate"      : hit_rate,
            "ci_low"        : ci_low*100,
            "ci_high"       : ci_high*100,
            "miss_mean"     : miss_mean,
            "miss_std"      : miss_std,
            "miss_median"   : miss_med,
            "miss_95th"     : miss_95,
            "all_miss_mean" : all_miss_mean,
            "all_miss_std"  : all_miss_std,
            "peak_accel_median" : peak_med,
            "avg_accel_median"  : avg_med,
            "saturation_mean"   : sat_mean,
            "saturation_median" : sat_med,
            "tti_mean"          : tti_mean,
            "tti_std"           : tti_std,
            "termination_counts": term_counts,
            "motion_breakdown"  : motion_breakdown,
            "convergence"       : convergence[mode]
        }

    #PRINT REPORT HEADER
    print("\n" + "=" * 60)
    print("MONTE CARLO SUMMARY REPORT")
    print(f"Trials per mode: {n_trials}")
    print("="*60)

    #PRINT REPORT WITH ONE BLOCK PER MODE
    for mode in modes:
        s = summary[mode]
        print(f"\n--- {mode} ---")
        print(f"  Intercept Probability : {s['hit_rate']:.1f}%  "
              f"(95% CI: {s['ci_low']:.1f}% - {s['ci_high']:.1f}%)")
        print(f"  Miss Distance (misses only):")
        print(f"      Mean   : {s['miss_mean']:.2f} m")
        print(f"      Std    : {s['miss_std']:.2f} m")
        print(f"      Median : {s['miss_median']:.2f} m")
        print(f"      95th % : {s['miss_95th']:.2f} m")
        print(f"  Miss Distance (all trials):")
        print(f"      Mean   : {s['all_miss_mean']:.2f} m")
        print(f"      Std    : {s['all_miss_std']:.2f} m")
        print(f"  Acceleration:")
        print(f"      Median Peak : {s['peak_accel_median']:.2f} m/s^2")
        print(f"      Median Avg  : {s['avg_accel_median']:.2f} m/s^2")
        print(f"  Saturation Fraction:")
        print(f"      Mean   : {s['saturation_mean']*100:.1f}%")
        print(f"      Median : {s['saturation_median']*100:.1f}%")
        print(f"  Time-to-Intercept (hits only):")
        if not np.isnan(s['tti_mean']):
            print(f"      Mean   : {s['tti_mean']:.2f} s")
            print(f"      Std    : {s['tti_std']:.2f} s")
        else:
            print(f"      N/A (no hits)")
        print(f"  Termination Reasons:")
        for reason, count in s["termination_counts"].items():
            print(f"      {reason:<18}: {count}  ({count/s['n']*100:.1f}%)")
        print(f"  Hit Rate by Motion Model:")
        for mt, label in [("constant_velocity", "CV"),
                          ("constant_acceleration", "CA"),
                          ("weaving", "WE")]:
            if mt in s["motion_breakdown"]:
                bd = s["motion_breakdown"][mt]
                print(f"      {label}: {bd['hit_rate']:.1f}%  (n={bd['n']})")
            else:
                print(f"      {label}: N/A (n=0)")
        print(f"  Convergence (running hit rate by trial count):")
        for c in s["convergence"]:
            print(f"      n={c['n']:>4}: {c['hit_rate']:.1f}%")
    
    #CROSS MODE COMPARISON FOR HIT RATE BY GUIDANCE LAW PER MOTION MODEL
    print("\n" + "-"*60)
    print("Hit Rate by Guidance Law per Motion Model: ")
    for mt, label in [("constant_velocity", "CV"), 
                      ("constant_acceleration", "CA"),
                      ("weaving", "Weave")]:
        parts = []
        for mode in modes:
            bd = summary[mode]['motion_breakdown'].get(mt, {"hit_rate":0})
            parts.append(f"{mode}: {bd['hit_rate']:.1f}%")
        print(f"    {label}: " + "  |   ".join(parts))
    print("-"*60 + "\n")

    return summary