import numpy as np
#IMPORT CLASSES
from Config.settings import settings
from Simulation.simulate import run_simulator
from Visualization.plot_trajectory import plot_3d_trajectory
kill_radius = settings.kill_radius

#NO NEED FOR CLASS, CAN JUST USE FUNCTION
def run_simulation():
    #SHOW USER OPTIONS FOR GUIDANCE MODE
    print("\n=== Missiel Guidance Simulation ===")
    print("Choose guidance mode: ")
    print("1. Proportional Navigation (PN)")
    print("2. Augmented Proportional Navigation (APN)")
    print("3. Zero Effort Miss (ZEM)")
    print("4. Real Life Tracking Simulation")

    #GET USER INPUT AND VALIDATE
    choice = input("Enter choice (1-4): ").strip()
    while choice not in ["1", "2", "3", "4"]:
        choice = input("Invalid choice. Enter choice (1-4): ").strip()
    
    #SELECT GUIDANCE MODE
    if choice == '1':
        guidance_mode = "PN"
    elif choice == '2':
        guidance_mode = "APN"
    elif choice == '3':
        guidance_mode = "ZEM"
    elif choice == '4':
        guidance_mode = "REAL"
    else:
        print("Invalid choice. Defaulting to PN.")
        guidance_mode = "PN"
    
    #STORE GUIDANCE MODE
    settings.guidance_mode = guidance_mode

    #RUN SIMULATION
    result = run_simulator(settings)

    #PRINT SUMMARY
    print("\n=== Simulation Summary ===")
    print(f"Guidance Mode: {result['model']}")
    print(f"Hit: {result['hit']}")
    print(f"Miss Distance: {result['miss_distance']:.3f} m")
    print(f"Final Time: {result['t_final']:.3f} s")
    print(f"Peak Acceleration: {result['peak_accel']:.3f} m/s^2")
    print(f"Average Acceleration: {result['avg_accel']:.3f} m/s^2")

    #PLOT TRAJECTORY
    plot_3d_trajectory(result['history'], kill_radius)

    return result
