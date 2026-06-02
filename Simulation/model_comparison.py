from simulate import run_simulation
from Config.settings import settings


def compare_guidance_modes(dt, t_max, kill_radius, max_accel, tau, N):
    #SETUP AMOUNT OF MODES, AND INITIALIZE RESULTS AS BLANK
    modes = ["PN", "APN", "ZEM"]
    results = {}

    #TABLE FORMAT
    print("\n=== Guidance Law Comparison ===")
    print(f"{'Mode':<6} | {'Miss (m)':<10} | {'Hit':<5} | {'Peak Accel':<12} | {'Avg Accel':<12} | {'t_final (s)':<10}")
    print("-"*70)

    #SIMULATION CALCULATIONS
    for mode in modes:
        settings.guidance_mode = mode
        out = run_simulation(settings)
        results[mode] = out

        #SHOW SIMULATION RESULTS IN FORMAT
        print(f"{mode:<6} | "
              f"{out['miss_distance']:<10.3f} | "
              f"{str(out['hit']):<5} | "
              f"{out['peak_accel']:<12.3f} | "
              f"{out['avg_accel']:<12.3f} | "
              f"{out['t_final']:<10.3f}")
        
    print("\nComparison complete.\n")
    return results