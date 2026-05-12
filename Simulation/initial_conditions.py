#Initial conditions for the simulation, including missile and interceptor parameters, and environmental conditions.
import math
import serial
import time
class InitialConditions:
    def __init__(self, port = "COM4", baudrate = 115200):
        self.port = port
        self.baudrate = baudrate

    #INITIAL HEADING FUNCTION
    def read_gimball_angles(self):
        try:
            #OPEN SERIAL PORT AND READ DATA
            ser = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)  # WAIT FOR SERIAL CONNECTION TO ESTABLISH
            ser.write(b"GET\n")#REQUEST ANGLES
            line = ser.readline().decode().strip()
            yaw_deg, pitch_deg = map(float, line.split())
            return math.radians(yaw_deg), math.radians(pitch_deg)
        except:
            print("Gimball read failed. Falling back to manual input.")
            yaw_deg = float(input("Enter interceptor yaw angle (degrees): "))
            pitch_deg = float(input("Enter interceptor pitch angle (degrees): "))
            return math.radians(yaw_deg), math.radians(pitch_deg)
    
    #INTERCEPTOR IC's
    def build_interceptor(self):
        Vi = float(input("Enter an interceptor speed (m/s): "))
        yaw_rad, pitch_rad = self.read_gimball_angles()
        direction_vector = [
            math.cos(pitch_rad) * math.cos(yaw_rad), #X/i
            math.cos(pitch_rad) * math.sin(yaw_rad), #Y/j
            math.sin(pitch_rad) #Z/k
        ]
        ri0 = [0, 0, 0] #INTERCEPTOR STARTING POSITION
        vi0 = [Vi * d for d in direction_vector] #INTERCEPTOR INITIAL VELOCITY VECTOR
        return ri0, vi0
    
    #TARGET IC's
    def build_target(self):
        Vt = float(input("Enter a target speed (m/s): "))
        yaw_deg = float(input("Enter target yaw angle (degrees): "))
        pitch_deg = float(input("Enter target pitch angle (degrees): "))
        yaw_rad = math.radians(yaw_deg)
        pitch_rad = math.radians(pitch_deg)
        direction_vector = [
            math.cos(pitch_rad) * math.cos(yaw_rad), #X/i
            math.cos(pitch_rad) * math.sin(yaw_rad), #Y/j
            math.sin(pitch_rad) #Z/k
        ]
        rt0 = [1000, 0, 0] #TARGET STARTING POSITION
        vt0 = [Vt * d for d in direction_vector] #TARGET INITIAL VELOCITY VECTOR
        return rt0, vt0

