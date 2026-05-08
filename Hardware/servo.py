#PURPOSE IS TO CONTROL SERVO

#IMPORT SERIAL AND TIME
import math
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

