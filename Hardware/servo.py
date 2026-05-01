#PURPOSE IS TO CONTROL SERVO

#IMPORT SERIAL AND TIME
import serial
import time
class ServoController:
    #INITIALIZE AND GET COMMUNICATION READY
    def __init__(self, port="COM4", buad=115200):
        self.ser = serial.Serial(port, buad, timeout=1)
        time.sleep(2)  # Wait for the serial connection to initialize
    #SET THE SERVO ANGLE BASED ON INPUTS
    def set_servo_angle(self, az_deg, el_deg):
        msg = f"{az_deg:.2f},{el_deg:.2f}\n"
        self.ser.write(msg.encode("utf-8"))
    #CLOSE THE SERIAL CONNECTION
    def close(self):
        self.ser.close()

#TEST USING THE CLASS TO ROTATE SERVO TO 15 DEGREES, WE ONLY HAVE ONE SERVO
servo = ServoController()
if input("Do you want to test the servo? (y/n): ").lower() == "y":
    try:
        servo.set_servo_angle(105, 0) 
        print("Moved to 75 degrees")
        time.sleep(5)
        servo.set_servo_angle(75, 0)
        print("Moved to 75 degrees")
        time.sleep(5)
    except KeyboardInterrupt:
        print("Exiting")
    finally:
        servo.close()