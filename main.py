#IMPORT LIBRARIES
import time
import numpy as np
#IMPORT CLASSES
from Config.settings import settings
from Hardware.gimbal_tracking import run_gimbal_tracking
from Hardware.gimbal_calibration import run_gimbal_calibration
from Config.settings_menu import run_settings_menu
from Simulation import initial_conditions
from Simulation.initial_conditions import InitialConditions
from Simulation.recorded_motion import RecordedTrajectory
from Simulation.run_simulation import run_simulation
from Simulation.model_comparison import run_comparison
from Simulation.monte_carlo import run_monte_carlo, summarize_monte_carlo
from Simulation.simulate import run_simulator
from Visualization.plot_monte_carlo import plot_monte_carlo
from Simulation.menu_sweep import menu_sweep
from Simulation.validate_pn import run_validation
from Visualization.plot_trajectory import plot_3d_trajectory
from Visualization.plot_validation import plot_validation
from Visualization.plot_guidance import plot_guidance_analysis
from csv_export import export_monte_carlo_csv
from Sensors.motion_recorder import record_batch, load_recording_pool
from Sensors.motion_recorder import record_batch, load_recording_pool, manage_recordings
from Simulation.validate_apn import run_validation as run_apn_validation
from Detection_Data_Processing.stereo_plane_analysis import vid_analysis
from Simulation.xyz_to_angles import xyz_to_angles


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
        print("7. PN Validation logic graph")
        print("8. APN Validation logic graph")
        print("9. Settings")
        print("10. Stereo Plane Analysis (single video)")
        print("11. Monte Carlo with recorded plane motion model")
        print("12. Record Target Motion Library(non-plane)")
        print("13. Manage/Delete Recorded Clips")
        print("14. Monte-Carlo on Recorded Motion")
        print("15. Exit")
        choice = input("Enter your choice (1-15): ").strip()
        while choice not in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12","13","14","15"]: 
            print("Invalid input. Please enter a number between 1 and 15")
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
            #EKF / SENSOR NOISE MODE
            ekf_choice = input("Enable EKF state estimation with sensor noise? (y/n): ").strip().lower()
            settings.use_ekf = (ekf_choice == 'y')
            if settings.use_ekf:
                imu_choice = input("Use real IMU hardware instead of synthetic noise? (y/n): ").strip().lower()
                settings.use_imu = (imu_choice == 'y')
            else:
                settings.use_imu = False
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
            results, ic = run_apn_validation()
            plot_validation(results, ic)
        elif choice == "9":
            run_settings_menu()
        elif choice == "10":
            video_results = vid_analysis(settings)

            if video_results is None:
                print("Stereo analysis returned no data. Check video paths")
                continue

            valid_results = [r for r in video_results if all(np.isfinite(r[key]) for key in ("timestamp_s", "x", "y", "z"))]
            if not valid_results:
                print("No finite 3D positions were produced, cannot run the interception")
                continue

            print(f"Using {len(valid_results)} valid recorded positions")
            parsed_data = xyz_to_angles(valid_results)
            timestamps = [r["timestamp"] for r in parsed_data]
            azimuths = [r["angle_x"] for r in parsed_data]
            elevations = [r["angle_y"] for r in parsed_data]
            ranges = [r["range_m"] for r in parsed_data]

            trajectory = RecordedTrajectory(
                timestamps,
                azimuths,
                elevations,
                ranges,
                initial_range_m=ranges[0],
                time_scale=1.0,
            )

            recorded_target_data = {
                "initial_position": trajectory.position(0.0).tolist(),
                "initial_velocity": trajectory.velocity(0.0).tolist(),
                "motion_model": "recorded",
                "params": {"trajectory": trajectory},
            }

            initial_conditions = InitialConditions()
            ri0, vi0 = initial_conditions.build_interceptor()

            ic_override = {
                "ri0" : ri0,
                "vi0" : vi0,
                "target_data" : recorded_target_data,
            }
            settings.target_motion = "recorded"
            settings.recorded_lookahead = float(np.median(np.diff(timestamps)))

            results = run_simulator(settings, ic_override = ic_override)
            print("\n=== Single Recorded-Path Intercept ===")
            print(f"Guidance Mode: {results['model']}")
            print(f"Hit: {results['hit']}")
            print(f"Miss Distance: {results['miss_distance']:.3f} m")
            print(f"Final Time: {results['t_final']:.3f} s")
            print(f"Termination: {results['termination_reason']}")

            plot_3d_trajectory(results["history"])
            plot_guidance_analysis(
                results["history"],
                title_suffix=f" {results['model']} recorded-path run",
            )

        elif choice == "11":
            ekf_choice = input("Enable EKF state estimation with sensor noise (y/n): ").strip().lower()
            settings.use_ekf = ekf_choice == 'y'
            results = vid_analysis(settings)
            if results is None:
                print("Stereo analysis did not return data. Check video paths in Settings")
                continue
            valid_results = [r for r in results if all(np.isfinite(r[key]) for key in ("timestamp_s", "x", "y", "z"))]
            print(f"Skipping {len(results) - len(valid_results)} rows without finite XYZ")
            parsed_data = xyz_to_angles(valid_results)
            n_trials = int(input("Number of Monte Carlo trials: "))
            seed = int(input("Random seed: ").strip())
            monte_carlo_results = run_monte_carlo(n_trials = n_trials, master_seed = seed, ic_overrides = {"recordings_pool" : [parsed_data]})
            summary = summarize_monte_carlo(monte_carlo_results)
            plot_monte_carlo(monte_carlo_results, summary)
        elif choice == "12":
            record_batch()
        elif choice == "13":
            manage_recordings()
        elif choice == "14":
            #LOAD POOL
            pool = load_recording_pool()
            #IF NO POOL THEN TELL USER TO BEGIN POOL
            if not pool:
                print("No recorded clips found. Use option 9 to record a library first")
            else:
                print(f"Loaded {len(pool)} recorded clip(s).")
                #DETERMINE TRIALS(OR LACK OF INPUT) AND RESET TO START
                settings.guidance_mode = "PN"
                n_trials = input("Enter number of trials per guidance mode (default 500): ").strip()
                if n_trials == "":
                    n_trials = 500
                else:
                    #GET TRIAL NUMBER
                    try:
                        n_trials = int(n_trials)
                        if n_trials <= 0:
                            print("Must be positive. Using default 500")
                            n_trials = 500
                    except ValueError:
                        print("Invalid input. Using default 500.")
                        n_trials = 500
                #GET SEED FOR RUN FOR REPEATIBILITY
                seed_input = input("Enter random seed (default 0): ").strip()
                if seed_input == "":
                    seed = 0
                else:
                    try:
                        seed = int(seed_input)
                    except ValueError:
                        print("Invalid input. Using default seed 0")
                        seed = 0

                #GET RUN DETAILS
                initial_range_m = float(input("Enter starting engagement range (m), real range curves get scaled to start here: ").strip() or 1000.0)
                time_scale = float(input("Enter time-scale factor (1.0 = as-recorded): ").strip() or 1.0)
                if time_scale == "":
                    time_scale = 1.0
                    break
                elif time_scale < 0:
                    print("Time scale must be positive. Try again")
                    time_scale = input("Enter time-scale factor")
                    
                ekf_choice = input("Enable EKF state estimation with sensor noise? (y/n): ").strip().lower()
                settings.use_ekf = (ekf_choice == 'y')
                if settings.use_ekf:
                    imu_choice = input("Use real IMU hardware instead of synthetic noise? (y/n): ").strip().lower()
                    settings.use_imu = (imu_choice == 'y')
                else:
                    settings.use_imu = False

                ic_overrides = {
                    "recordings_pool": pool,
                    "initial_range_m": initial_range_m,
                    "time_scale": time_scale,
                }
                mc_output = run_monte_carlo(n_trials = n_trials, master_seed = seed, ic_overrides = ic_overrides)
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
                    mode = mode_dict.get(mode_choice)
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
                    print("Do you want a csv export?(y/n):")
                    export = input("").strip().lower()
                    if export == 'y':
                        export_monte_carlo_csv(mc_output, summary)
        else:
            exit_program()

#IMPLEMENTATION OF MAIN CODE
if __name__ == "__main__":
    main()