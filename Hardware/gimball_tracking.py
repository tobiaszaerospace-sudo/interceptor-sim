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