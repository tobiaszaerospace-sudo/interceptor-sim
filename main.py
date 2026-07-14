#IMPORT LIBRARIES
import time
#IMPORT CLASSES
from Config.settings import settings
from Hardware.gimbal_tracking import run_gimbal_tracking
from Hardware.gimbal_calibration import run_gimbal_calibration
from Config.settings_menu import run_settings_menu
from Simulation.run_simulation import run_simulation
from Simulation.model_comparison import run_comparison
from Simulation.monte_carlo import run_monte_carlo, summarize_monte_carlo
from Visualization.plot_monte_carlo import plot_monte_carlo
from Simulation.menu_sweep import menu_sweep
from Simulation.validate_pn import run_validation
from Visualization.plot_trajectory import plot_3d_trajectory
from Visualization.plot_validation import plot_validation
from Visualization.plot_guidance import plot_guidance_analysis
from csv_export import export_monte_carlo_csv

#OPTION 5: EXIT
def exit_program():
    print("Exiting program. Goodbye!")
    time.sleep(.3)
    raise SystemExit

#ACTUAL MAIN CODE
def main():
    while True:
        print("\n --- MAIN MENU --- ")
        print("1. Gimbal Tracking")
        print("2. Interceptor Simulation")
        print("3. Gimbal Calibration")
        print("4. Model Comparison")
        print("5. Monte-Carlo Simulation")
        print("6. Monte-Carlo across one variable(Sweep)")
        print("7. Validation logic graph")
        print("8. Settings")
        print("9. Exit")
        choice = input("Enter your choice (1-9): ").strip()
        while choice not in ["1", "2", "3", "4", "5", "6", "7", "8", "9"]:
            print("Invalid input. Please enter a number between 1 and 9.")
            choice = input("Enter your choice (1-9): ").strip()
        if choice == "1":
            run_gimbal_tracking()
        elif choice == "2":
            run_simulation()
        elif choice == "3":
            run_gimbal_calibration()
        elif choice == "4":
            run_comparison()
        elif choice == "5":
            settings.guidance_mode = "PN"
            n_trials = input("Enter number of trials per guidance mode (default 500): ").strip()
            if n_trials == "":
                n_trials = 500
            else:
                try:
                    n_trials = int(n_trials)
                    if n_trials <= 0:
                        print("Must be positive. Using defulat 500")
                        n_trials = 500
                except ValueError:
                    print("Invalid input. Using default 500.")
                    n_trials = 500
            seed_input = input("Enter random seed (default 0): ").strip()
            if seed_input == "":
                seed = 0
            else:
                try:
                    seed = int(seed_input)
                except ValueError:
                    print("Invalid input. Using default seed 0")
                    seed = 0                
            mc_output = run_monte_carlo(n_trials = n_trials, master_seed = seed)
            summary = summarize_monte_carlo(mc_output)
            plot_monte_carlo(mc_output, summary)
            settings.guidance_mode = "PN"
            #AFTER PLOTTING ASK IF THEY WANT TO SEE A SINGLE TRIAL
            view = input("View a sample trajectory? (y/n): ").strip().lower()
            if view == 'y':
                print("Select mode:  1) PN   2) APN   3) ZEM")
                mode_choice = input(" Choice: ").strip()
                mode_dict = {
                    "1": "PN",
                    "2": "APN",
                    "3": "ZEM"
                }
                mode = mode_dict.get(mode_choice, )
                available = list(mc_output['sample_trajectories'][mode].keys())
                print(f"Available trial indeces: {available}")
                trial_input = input("Select trial index: ").strip()
                try:
                    trial_idx = int(trial_input)
                except ValueError:
                    trial_idx = available[0]
                
                history = mc_output['sample_trajectories'][mode][trial_idx]
                plot_3d_trajectory(history)
                plot_guidance_analysis(history, title_suffix = f" {mode} Trial {trial_idx}")
                print("Do you want a csv export?(y/n):" )
                export = input("").strip().lower()
                if export == 'y':
                    export_monte_carlo_csv(mc_output, summary)

        elif choice == "6":
            menu_sweep()
        elif choice == "7":
            results, ic = run_validation()
            plot_validation(results, ic)
        elif choice == "8":
            run_settings_menu()
        else:
            exit_program()

#IMPLEMENTATION OF MAIN CODE
if __name__ == "__main__":
    main()
