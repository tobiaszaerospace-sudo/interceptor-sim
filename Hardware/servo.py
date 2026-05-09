#PURPOSE IS TO CONTROL SERVO

#IMPORT SERIAL AND TIME
import math
import serial
import time
class ServoController:
    #INITIALIZE AND GET COMMUNICATION READY
    def __init__(self, port="COM4", baud=115200):
        self.ser = serial.Serial(port, baud, timeout=1)
        time.sleep(2)  # Wait for the serial connection to initialize
    #SET THE SERVO ANGLE BASED ON INPUTS
    def set_servo_angle(self, az_deg, el_deg):
        az_deg = max(-90.0, min(90.0, az_deg))  # Clamp azimuth to [-90, 90]
        el_deg = max(-90.0, min(90.0, el_deg))  # Clamp elevation to [-90, 90]
        az_deg += 90.0  # Convert from -90 to 90 range to 0 to 180 range
        el_deg += 90.0  # Convert from -90 to 90 range to
        msg = f"{az_deg:.2f},{el_deg:.2f}\n"
        self.ser.write(msg.encode("utf-8"))
    #CLOSE THE SERIAL CONNECTION
    def close(self):
        self.ser.close()

