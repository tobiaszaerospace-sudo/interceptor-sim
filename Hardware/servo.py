#PURPOSE IS TO CONTROL SERVO

#IMPORT SERIAL AND TIME
import serial
import time

class ServoController:
    def __init__(self, port="COM4", buad=115200):
        self.ser = serial.Serial(port, buad, timeout=1)
        time.sleep(2)  # Wait for the serial connection to initialize

    def set_servo_angle(self, az_deg, el_deg):
        msg = f"{az_deg:.2f},{el_deg:.2f}\n"
        self.ser.write(msg.encode("utf-8"))
    
    def close(self):
        self.ser.close()