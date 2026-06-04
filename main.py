#IMPORT LIBRARIES
import time
#IMPORT CLASSES
from Config.settings import settings
from Hardware.gimbal_tracking import run_gimbal_tracking
from Hardware.gimbal_calibration import run_gimbal_calibration
from Config.settings_menu import run_settings_menu
from Simulation.run_simulation import run_simulation
from Simulation.model_comparison import run_comparison

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
        print("5. Settings")
        print("6. Exit")
        choice = input("Enter your choice (1-6): ").strip()
        while choice not in ["1", "2", "3", "4", "5", "6"]:
            print("Invalid input. Please enter a number between 1 and 6.")
            choice = input("Enter your choice (1-6): ").strip()
        if choice == "1":
            run_gimbal_tracking()
        elif choice == "2":
            run_simulation()
        elif choice == "3":
            run_gimbal_calibration()
        elif choice == "4":
            run_comparison()
        elif choice == "5":
            run_settings_menu()
        else:
            exit_program()

#IMPLEMENTATION OF MAIN CODE
if __name__ == "__main__":
    main()
