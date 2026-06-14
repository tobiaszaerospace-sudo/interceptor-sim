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
        print("6. Settings")
        print("7. Exit")
        choice = input("Enter your choice (1-7): ").strip()
        while choice not in ["1", "2", "3", "4", "5", "6", "7"]:
            print("Invalid input. Please enter a number between 1 and 7.")
            choice = input("Enter your choice (1-7): ").strip()
        if choice == "1":
            run_gimbal_tracking()
        elif choice == "2":
            run_simulation()
        elif choice == "3":
            run_gimbal_calibration()
        elif choice == "4":
            run_comparison()
        elif choice == "5":
            n_trials = input("Enter number of tirals per guidance mode (default 500): ").strip()
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
            seed_input = input("Enter random seed (defualt 0): ").strip()
            if seed_input == "":
                seed = 0
            else:
                try:
                    seed = int(seed_input)
                except ValueError:
                    print("Invalid input. Using default seed 0")
                    seed = 0                
            mc_output = run_monte_carlo(n_trials = n_trials, master_seed = seed)
            summarize_monte_carlo(mc_output)
        elif choice == "6":
            run_settings_menu()
        else:
            exit_program()

#IMPLEMENTATION OF MAIN CODE
if __name__ == "__main__":
    main()
