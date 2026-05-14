import cv2
from Hardware.servo import ServoController
from Config.settings import settings
import numpy as np

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