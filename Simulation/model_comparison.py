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
    #EKF MODE
    ekf_choice = input("Enable EKF state estimation with sensor noise for this comparison? (y/n): ").strip().lower()
    settings.use_ekf = (ekf_choice == 'y')
    if settings.use_ekf:
        imu_choice = input("Use real IMU hardware instead of synthetic noise? (y/n): ").strip().lower()
        settings.use_imu = (imu_choice == 'y')
        noise_seed = int(np.random.default_rng().integers(0, 1_000_000))
        print(f"(using noise seed {noise_seed} for all three modes)")
    else:
        settings.use_imu = False
        noise_seed = None
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
        results[mode] = run_simulator(settings, ic_override = fixed_ic, noise_seed = noise_seed)
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