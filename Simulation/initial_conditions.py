#Initial conditions for the simulation, including missile and interceptor parameters, and environmental conditions.
import math
import time
from Config.settings import settings
#BLOCK AGAINST IMPORT ISSUES CRASHING
try:
    import serial
except ImportError:
    serial = None

#FUNCTION FOR VALIDATING NUMERIC VALUES
def get_float(prompt):
    while True:
        try:
            return float(input(prompt))
        except ValueError:
            print("Invalid input. Enter a numeric value.")
#INITIAL CONDITIONS CLASS FOR SIMULATION
class InitialConditions:
    def __init__(self, port = "COM4", baudrate = 115200):
        self.port = port
        self.baudrate = baudrate

    #INITIAL HEADING FUNCTION
    def read_gimball_angles(self):
        #CHECK IF SERIAL MODULE ISN'T THERE FIRST
        if serial is None:
            print("Gimball read failed. Falling back to manual input.")
            yaw_deg = get_float("Enter interceptor yaw angle (degrees): ")
            pitch_deg = get_float("Enter interceptor pitch angle (degrees): ")
            return math.radians(yaw_deg), math.radians(pitch_deg)
        try:
            #OPEN SERIAL PORT AND READ DATA
            ser = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)  # WAIT FOR SERIAL CONNECTION TO ESTABLISH
            ser.write(b"GET\n")#REQUEST ANGLES
            #DECODE ANGLES FROM SERIAL INPUT
            line = ser.readline().decode().strip()
            yaw_deg, pitch_deg = map(float, line.split())
            return math.radians(yaw_deg), math.radians(pitch_deg) #CONVERT TO RADIANS AND RETURN
        #IF SERIAL READING FAILS, FALL BACK TO MANUAL INPUT
        except:
            print("Gimball read failed. Falling back to manual input.")
            yaw_deg = get_float("Enter interceptor yaw angle (degrees): ")
            pitch_deg = get_float("Enter interceptor pitch angle (degrees): ")
            return math.radians(yaw_deg), math.radians(pitch_deg)
    
    #INTERCEPTOR IC's
    def build_interceptor(self):
        #GRAB SPEED FROM USER
        Vi = get_float("Enter an interceptor speed (m/s): ")
        #DETERMINE DIRECTION FROM GIMBALL OR MANUAL INPUT
        yaw_rad, pitch_rad = self.read_gimball_angles()
        #CONVERT TO VECTOR FORMAT
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
        #GRAB MOTION TYPE AND CHECK IT
        print("\n=== Select Target Motion Model ===")
        print("1. Constant Velocity")
        print("2. Constant Acceleration")
        print("3. Weaving")

        #PICK MOTION CHOICE
        motion_type = input("Enter choice (1-3): ").strip()
        if motion_type == "1":
            target_motion = "constant_velocity"
        elif motion_type == '2':
            target_motion = "constant_acceleration"
        elif motion_type == '3':
            target_motion = 'weaving'
        else:
            print("Invalid choice, defaulting to constant velocity")
            target_motion = "constant_velocity"
        
        #STORE CHOICE SO INITIAL CONDITIONS CAN USE IT
        settings.target_motion = target_motion

        #DIRECTION AND SPEED INPUTS
        Vt = get_float("Enter a target speed (m/s): ")
        while Vt < 0:
            Vt = get_float("Speed must be non-negative. Re-enter: ")
        yaw_deg = get_float("Enter target yaw angle (degrees): ")
        pitch_deg = get_float("Enter target pitch angle (degrees): ")
        yaw_rad = math.radians(yaw_deg)
        pitch_rad = math.radians(pitch_deg)
        #CONVERSION TO VECTOR FORMAT
        direction_vector = [
            math.cos(pitch_rad) * math.cos(yaw_rad), #X/i
            math.cos(pitch_rad) * math.sin(yaw_rad), #Y/j
            math.sin(pitch_rad) #Z/k
        ]
        rt0 = [1000, 0, 0] #TARGET STARTING POSITION
        vt0 = [Vt * d for d in direction_vector] #TARGET INITIAL VELOCITY VECTOR
        #MOTION MODEL PARAMETERS
        params = {}
        #CONSTANT VELOCITY DOESN'T NEED PARAMETERS, BUT OTHER MODELS DO
        #CONSTANT ACCELERATION, NEED VALUES FOR EACH DIRECTION
        if target_motion == "constant_acceleration":
            ax = get_float("Enter target acceleration in X direction (m/s^2): ")
            ay = get_float("Enter target acceleration in Y direction (m/s^2): ")
            az = get_float("Enter target acceleration in Z direction (m/s^2): ")
            params['accel'] = [ax, ay, az]
        #WEAVING MOTION, NEED AMPLITUDE, FREQUENCY, AND AXIS
        elif target_motion == "weaving":
            params['amplitude'] = get_float("Enter weave amplitude (m/s^2): ")
            while params['amplitude'] < 0:
                params['amplitude'] = get_float("Value must be non-negative. Re-enter: ")
            params['omega'] = get_float("Enter weave frequency (rad/s): ")
            while params['omega'] < 0:
                params['omega'] = get_float("Value must be non-negative. Re-enter: ")
            #GRAB AND CHECK AXIS INPUT  
            axis = input("Enter weave axis (x, y, or z): ").strip().lower()
            if axis not in ['x', 'y', 'z']:
                print("Invalid weave axis. Defaulting to y-axis.")
                axis = 'y'
            params['axis'] = axis


        return rt0, vt0, target_motion, params

