#IMPORT LIBRARIES
import numpy as np
#IMPORT CLASSES
from Config.settings import settings
from Simulation.simulate import run_simulator
from Simulation.initial_conditions import InitialConditions
from Visualization.plot_trajectory import plot_3d_comparison
from Simulation.run_simulation import run_simulation

#NO NEED FOR CLASS, JUST FUNCTION FOR COMPARISON
def run_comparison():
    #GENERATE INITIAL CONDITIOSN ONCE
    ic = InitialConditions()
    ri0, vi0 = ic.build_interceptor()
    target_data = ic.build_target()
    fixed_ic = {
        "ri0" : ri0,
        "vi0" : vi0,
        "target_data" : target_data,
    }
    
    #RUN ALL THREE MODES
    modes = ["PN", "APN", "ZEM"]
    results = {}
    for mode in modes:
        settings.guidance_mode = mode
        results[mode] = run_simulator(settings, ic_override = fixed_ic, save_history = True, N = settings.N, N_zem = settings.N_zem)
    #RESET TO DEFAULT - TRYING TO FIX BUG
    settings.guidance_mode = "PN"

    #PRINT SUMMARY TABLE
    print("\n=== Guidance Law Comparison ===")
    print(f"{'Mode':<6} | {'Miss (m)':<10} | {'Hit':<5} | {'Peak Accel':<12} | {'Avg Accel':<12} | {'t_final (s)':<10}")
    print("-" * 70)
    #NOW PRINT RESULTS
    for mode in modes:
        out = results[mode]
        print(f"{mode:<6} | "
              f"{out['miss_distance']:<10.3f} | "
              f"{str(out['hit']):<5} | "
              f"{out['peak_accel']:<12.3f} | "
              f"{out['avg_accel']:<12.3f} | "
              f"{out['t_final']:<10.3f}")
        print("-" * 70)

    #PLOT COMBINED TRAJECTORIES
    plot_3d_comparison(results)

    #RETURN RESULTS
    return results