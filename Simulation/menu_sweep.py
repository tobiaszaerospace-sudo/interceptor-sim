#MENU FOR MONTE CARLO SWEEP
#IMPORT FILES
from Simulation.run_sweep import run_sweep, build_sweep_levels, resolve_trials_per_step, Sweep_variables
from Visualization.plot_sweep import plot_sweep

def menu_sweep():
#GET VARIABLES
    var_keys = list(Sweep_variables.keys())
    print("\nSelect variable to sweep: ")

    #DISPLAY MENU
    for i, key in enumerate(var_keys):
        s = Sweep_variables[key]
        u = f" {s['units']}" if s['units'] else ""
        b = str(s['baseline']) if s['baseline'] is not None else "randomized"
        print(f"    {i+1}. {s['label']}    (baseline={b}{u})")

    #GET USER CHOICE
    var_choice = input(f"Enter choice (1-{len(var_keys)}): ").strip()

    #VALIDATE USER CHOICE
    while not var_choice.isdigit() or int(var_choice) not in range(1,len(var_keys)+1):
        var_choice = input("Invalid. Enter 1-{len(var_keys)}: ").strip()

    #STANDARDIZE RESPONSE
    var_name = var_keys[int(var_choice)-1]
    s = Sweep_variables[var_name]
    u = f" {s['units']}" if s['units'] else ""

    #DETERMINE LEVEL RANGE, PRESET OR CUSTOM
    print(f"Preset: {s['default_min']} to {s['default_max']}{u} in {s['default_steps']} steps")
    if input("Use preset? (y/n, defaulty): ").strip().lower() == 'n':
        #GRAB AND VALIDATE INPUTS
        try: 
            lo = float(input(f"  Min [{s['default_min']}]: ").strip() or s['default_min'])
        except ValueError: 
            lo = s['default_min']
        try: 
            hi = float(input(f"  Max [{s['default_max']}]: ").strip() or s['default_max'])
        except ValueError:
            hi = s['default_max']
        try:
            steps = int(input(f"  Steps [{s['default_steps']}]: ").strip() or s['default_steps'])
            if steps <2: 
                steps = s['default_steps']
        except ValueError:
            steps = s['default_steps']
        
        #DO LEVELS
        levels = build_sweep_levels(var_name, n_steps=steps, level_min=lo, level_max=hi)

    else:
        levels = build_sweep_levels(var_name)

    #NOW DO TRIAL COUNT BY N OR TARGET PRECISION
    #GRAB USER CHOICE AND VALIDATE
    print("Trial count \n1) Enter n directly  \n2) Enter target precision (+-pts)")
    tc=  input("Choise 1/2: ").strip()
    while tc not in ["1", "2"]:
        tc = input("Etner 1 or 2: ").strip()
    #FOR GIVEN N INPUT
    if tc == "1":
        try:
            n_raw = max(1, int(input("Trials per step (default 75): ").strip() or 75))
        except ValueError: 
            n_raw = 75
        #CALCULATION
        trials_per_step = resolve_trials_per_step("n", n_raw)
    #FOR GIVEN HALFWIDTH
    else:
        try:
            hw = max(.1, float(input("Target half-width in pts (default 10.0): ").strip() or 10.0))
        except ValueError:
            hw = 10.0
        try:
            p = float(input("Assumed hit rate for planning (default 0.5): ").strip() or 0.5)
            if not 0 < p < 1:
                p = .5
        except ValueError:
            p = 0.5
        
        #NOW DO COMPUTATION
        trials_per_step = resolve_trials_per_step("halfwidth", hw, p_assumed=p)

    #SEED INPUT
    try:
        seed = int(input("Random seed (default 0): ").strip() or 0)
    except ValueError:
        seed = 0
    
    #VERBOSE INPUT
    value = input("Do you want a readback? (y/n): ").lower()
    if value == 'y':
        verbose = True
    else:
        verbose = False

    #CALCULATION AND PLOT
    sweep_output = run_sweep(var_name, levels=levels, trials_per_step=trials_per_step, master_seed=seed, verbose=verbose)
    plot_sweep(sweep_output)