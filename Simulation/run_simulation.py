import numpy as np
#IMPORT CLASSES
from Config.settings import settings
from Simulation.simulate import run_simulator
from Visualization.plot_trajectory import plot_3d_trajectory
kill_radius = settings.kill_radius
from Visualization.plot_guidance import plot_guidance_analysis, plot_ekf_analysis
from Visualization.plot_prediction import plot_prediction_analysis

#NO NEED FOR CLASS, CAN JUST USE FUNCTION
def run_simulation():
    #SHOW USER OPTIONS FOR GUIDANCE MODE
    print("\n=== Missiel Guidance Simulation ===")
    print("Choose guidance mode: ")
    print("1. Proportional Navigation (PN)")
    print("2. Augmented Proportional Navigation (APN)")
    print("3. Zero Effort Miss (ZEM)")

    #GET USER INPUT AND VALIDATE
    choice = input("Enter choice (1-3): ").strip()
    while choice not in ["1", "2", "3"]:
        choice = input("Invalid choice. Enter choice (1-3): ").strip()
    
    #SELECT GUIDANCE MODE
    if choice == '1':
        guidance_mode = "PN"
    elif choice == '2':
        guidance_mode = "APN"
    elif choice == '3':
        guidance_mode = "ZEM"
    else:
        print("Invalid choice. Defaulting to PN.")
        guidance_mode = "PN"
    
    #STORE GUIDANCE MODE
    settings.guidance_mode = guidance_mode

    #EKF/SENSOR NOISE CODE
    ekf_choice = input("Enable EKF state estimation with sensor noise? (y/n): ").strip().lower()
    settings.use_ekf = (ekf_choice == "y")
    if settings.use_ekf:
        imu_choice = input("Use real IMU hardware instead of synthetic noise? (y/n): ").strip().lower()
        settings.use_imu = (imu_choice == "y")
    else:
        settings.use_imu = False
    
    #PHYSICAL GIMBAL
    gimbal_choice = input("Move physical gimbal during this run? (y/n): ").strip().lower()
    move_gimbal = (gimbal_choice == 'y')

    #RUN SIMULATION
    result = run_simulator(settings, move_gimbal = move_gimbal)

    #PRINT SUMMARY
    print("\n=== Simulation Summary ===")
    print(f"Guidance Mode: {result['model']}")
    print(f"Hit: {result['hit']}")
    print(f"Miss Distance: {result['miss_distance']:.3f} m")
    print(f"Final Time: {result['t_final']:.3f} s")
    print(f"Peak Acceleration: {result['peak_accel']:.3f} m/s^2")
    print(f"Average Acceleration: {result['avg_accel']:.3f} m/s^2")

    #PLOT TRAJECTORY
    plot_3d_trajectory(result['history'])
    #PLOT GUIDANCE ANALYSIS
    plot_guidance_analysis(result['history'], title_suffix = result['model'])
    #PLOT EKF TRUE VS ESTIMATE AND NEES
    plot_ekf_analysis(result['history'], title_suffix = result['model'])

    #RECORDED OPTION
    if settings.target_motion == 'recorded':
        plot_prediction_analysis(result['history'], lookahead = settings.recorded_lookahead, title_suffix = result['model'])

    return result
