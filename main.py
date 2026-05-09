#IMPORT LIBRARIES
import time
import cv2
import numpy as np
#IMPORT CLASSES
from Sensors.camera import Camera
from Sensors.tracking import Tracker
from Detection_Data_Processing.prediction import Prediction
from Detection_Data_Processing.los_computation import LOSComputer
from Hardware.servo import ServoController
from Config.settings import settings

#MAKE OPTION FUNCTIONS
#OPTION 1: TRACKING
def run_gimbal_tracking():
    print("Starting Gimbal Tracking...")
    #INITIALIZE CLASSES
    tracker = Tracker()
    servo = ServoController(port = settings.servo_port, baud = settings.servo_baud)
    los = LOSComputer(camera_fov_degrees=settings.camera_fov_x, image_width=settings.image_width, image_height=settings.image_height)
    #SHOW USER MENU FOR TRACKING METHOD
    print("\nSelect Prediction Method:")
    print("0: Zero-Order (Current Position Tracking)")
    print("1: First-Order (Velocity Only Prediction)")
    print("2: Second-Order (Velocity and Acceleration Prediction)")
    print("3: Adaptive (auto-switching)")
    #GRAB USER INPUT FOR PREDICTION METHOD
    mode = input("Enter mode (0-3): ").strip()
    #MAKE SURE IT'S A VALID OPTION
    while mode not in ["0", "1", "2", "3"]:
        print("Invalid input. Please enter 0, 1, 2, or 3.")
        mode = input("Enter mode (0-3): ").strip()
    print(f"Selected Mode: {mode}")
    #ROLLING BUFFER FOR FIRST 3 YOLO FRAMES
    from collections import deque
    frame_history = deque(maxlen=3)
    #TIME STEP
    time_step = 1/settings.fps
    future_time = .1 #100 MS AHEAD
    try:
        while True:
            data = tracker.process_frame()
            frame = data["frame"]
            yolo_det = data["yolo"]
            tag_det = data["apriltag"]
            if not yolo_det["valid"]:
                print("No valid YOLO detection. Skipping frame.")
                cv2.imshow("Tracking", frame)
                if cv2.waitKey(1) == 27:
                    break
                continue
            #GRAB YOLO CENTROID
            cx, cy = yolo_det["cx"], yolo_det["cy"]
            #APRILTAG ACCURACY LOGGING
            if tag_det["valid"]:
                tag_cx, tag_cy = tag_det["cx"], tag_det["cy"]
                error_x = cx - tag_cx
                error_y = cy - tag_cy
                print(f"YOLO vs AprilTag Error: X={error_x:.2f}, Y={error_y:.2f}")
            #ADD TO ROLLING BUFFER
            frame_history.append({"cx": cx, "cy": cy, "timestamp": time.time()})
            #IF WE DON'T HAVE ENOUGH FRAMES FOR PREDICTION, FALLBACK TO ZEROETH-ORDER
            if len(frame_history) < 3:
                pred_cx, pred_cy = cx, cy
            else:
                #STORE DATA
                frame1, frame2, frame3 = frame_history[0], frame_history[1], frame_history[2]
                #GRAB DATA
                predictor = Prediction(frame1, frame2, frame3, time_step)
                positions = predictor.get_position_data()
                velocity, acceleration = predictor.compute_velocity_acceleration(positions)
                #MAKE PREDICTION BASED ON MODE
                if mode == "0": #ZERO-ORDER
                    pred = predictor.zeroeth_order_prediction()
                elif mode == "1": #FIRST-ORDER
                    pred = predictor.first_order_prediction(velocity, future_time)
                elif mode == "2": #SECOND-ORDER
                    pred = predictor.second_order_prediction(velocity, acceleration, future_time)
                else: #ADAPTIVE
                    pred = predictor.adaptive_prediction(velocity, acceleration, future_time)
                #NOW STORE PREDICTION OUTPUT
                pred_cx, pred_cy = pred["future_cx"], pred["future_cy"]
            #COMPUTE LOS ANGLES FROM PREDICTED POSITION TO OUTPUT TO USER AND SERVOS
            los_angles = los.compute_los_angles(pred_cx, pred_cy)
            az, el = los_angles["angle_x"], los_angles["angle_y"]
            #TELL USER
            print(f"[YOLO] AZ: {az:.2f}°, EL: {el:.2f}°")
            #COMMAND SERVOS
            servo.set_servo_angle(az, el)
            #DRAW PREDICTED POINT ON FRAME FOR USER
            cv2.circle(frame, (int(pred_cx), int(pred_cy)), 6, (0, 0, 255), -1)
            cv2.imshow("Tracking", frame)
            #EXIT ON ESC KEY
            if cv2.waitKey(1) == 27:
                break
    except KeyboardInterrupt:
        print("\nTracking interrupted by user.")
        #TODO) ADD IN SWITCH TO SIMULATION IF 'S' IS PRESSED
    finally:
        #DESTROY ALL WINDOWS
        tracker.release()
        servo.close()
        cv2.destroyAllWindows()
        print("Gimball Tracking Stopped.")

#OPTION 2: SIMULATION
def run_interceptor_simulation():
    print("Starting Interceptor Simulation...")
    #TODO) IMPLEMENT SIMULATION MODE
    print("Simulation mode is not yet implemented. Please check back later.")

#OPTION 3: GIMBALL CALIBRATION
def run_gimbal_calibration():
    print("Starting Gimbal Calibration...")
    print("Use A/D for azimuth, W/S for elevation.")
    print("Press C to center. Press ESC to exit.\n")
    #DUMMY WINDOW SO WAITKEY WORKS AND ISN'T OVERLOADED
    cv2.namedWindow("Calibration")
    cv2.imshow("Calibration", np.zeros((200,200,3), dtype=np.uint8))
    #INITIALIZE SERVO
    servo = ServoController(port = settings.servo_port, baud = settings.servo_baud)
    az = 0
    el = 0
    try:
        while True:
            key = cv2.waitKey(1) & 0xFF
            if key == 27: #ESC
                break
            elif key == ord('a'):
                az -= 1
            elif key == ord('d'):
                az += 1
            elif key == ord('w'):
                el += 1
            elif key == ord('s'):
                el -= 1
            elif key == ord('c'):
                az, el = 0, 0
            #COMMAND SERVOS
            servo.set_servo_angle(az, el)
            #CLAMP ANGLES FOR DISPLAY
            az = max(-90, min(90, az))
            el = max(-90, min(90, el))
            print(f"Current Angles - AZ: {az}°, EL: {el}°")
    finally:
        servo.close()
        cv2.destroyAllWindows()
        print("Gimbal Calibration Complete.")

#OPTION 4: SETTINGS
def run_settings_menu():
    while True:
        #SHOW CURRENT SETTINGS TO USER
        print("\n --- SETTINGS MENU --- ")
        print(f"1. Camera FOV X: {settings.camera_fov_x}")
        print(f"2. Image Width: {settings.image_width}")
        print(f"3. Image Height: {settings.image_height}")
        print(f"4. Camera Index: {settings.camera_index}")
        print(f"5. FPS: {settings.fps}")
        print(f"6. Servo Port: {settings.servo_port}")
        print(f"7. Servo Baud: {settings.servo_baud}")
        print(f"8. YOLO Model Path: {settings.yolo_model_path}")
        print("9. Return to Main Menu")
        choice = input("Enter the number of the setting you want to change or exit program (1-9): ").strip()
        #VALIDATE INPUT
        while choice not in [str(i) for i in range(1, 10)]:
            print("Invalid input. Please enter a number between 1 and 9.")
            choice = input("Enter the number of the setting you want to change or exit program (1-9): ").strip()
        if choice == "9":
            print("Returning to Main Menu...")
            break
        #CAMERA FOV
        elif choice == "1":
            try:
                new_fov = float(input("Enter new Camera FOV X in degrees: ").strip())
                settings.camera_fov_x = new_fov
                print(f"Camera FOV X updated to {new_fov} degrees.")
            except ValueError:
                print("Invalid input. Please enter a valid number.")
        #IMAGE WIDTH
        elif choice == "2":
            try:
                new_width = int(input("Enter new Image Width in pixels: ").strip())
                settings.image_width = new_width
                print(f"Image Width updated to {new_width} pixels.")
            except ValueError:
                print("Invalid input. Please enter a valid integer.")
        #IMAGE HEIGHT
        elif choice == "3":
            try:
                new_height = int(input("Enter new Image Height in pixels: ").strip())
                settings.image_height = new_height
                print(f"Image Height updated to {new_height} pixels.")
            except ValueError:
                print("Invalid input. Please enter a valid integer.")
        #CAMERA INDEX
        elif choice == "4":
            try:
                new_index = int(input("Enter new Camera Index (integer): ").strip())
                settings.camera_index = new_index
                print(f"Camera Index updated to {new_index}.")
            except ValueError:
                print("Invalid input. Please enter a valid integer.")
        #FPS
        elif choice == "5":
            try:
                new_fps = int(input("Enter new FPS (integer): ").strip())
                settings.fps = new_fps
                print(f"FPS updated to {new_fps}.")
            except ValueError:
                print("Invalid input. Please enter a valid integer.")
        #SERVO PORT
        elif choice == "6":
            new_port = input("Enter new Servo Port (e.g., COM3 or /dev/ttyUSB0): ").strip()
            settings.servo_port = new_port
            print(f"Servo Port updated to {new_port}.")
        #SERVO BAUD
        elif choice == "7":
            try:
                new_baud = int(input("Enter new Servo Baud Rate (integer): ").strip())
                settings.servo_baud = new_baud
                print(f"Servo Baud Rate updated to {new_baud}.")
            except ValueError:
                print("Invalid input. Please enter a valid integer.")
        #YOLO MODEL PATH
        elif choice == "8":
            new_path = input("Enter new YOLO Model Path: ").strip()
            settings.yolo_model_path = new_path
            print(f"YOLO Model Path updated to {new_path}.")
        
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
        print("4. Settings")
        print("5. Exit")
        choice = input("Enter your choice (1-5): ").strip()
        while choice not in ["1", "2", "3", "4", "5"]:
            print("Invalid input. Please enter a number between 1 and 5.")
            choice = input("Enter your choice (1-5): ").strip()
        if choice == "1":
            run_gimbal_tracking()
        elif choice == "2":
            run_interceptor_simulation()
        elif choice == "3":
            run_gimbal_calibration()
        elif choice == "4":
            run_settings_menu()
        else:
            exit_program()

#IMPLEMENTATION OF MAIN CODE
if __name__ == "__main__":
    main()
