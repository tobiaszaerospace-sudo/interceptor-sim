#Initial conditions for the simulation, including missile and interceptor parameters, and environmental conditions.
import math
import time
from Config.settings import settings
import numpy as np
from Simulation.recorded_motion import RecordedTrajectory
from Sensors.motion_recorder import record_target_motion
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

#GET LOS DIRECTION VECTOR
def _unit_vector(self, az, el):
    return np.array([
        np.cos(el) * np.cos(az),
        np.cos(el) * np.sin(az),
        np.sin(el)
    ])


#INITIAL CONDITIONS CLASS FOR SIMULATION
class InitialConditions:
    def __init__(self, port = "COM4", baudrate = 115200):
        self.port = settings.serial_port
        self.baudrate = settings.baudrate

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
            ser.setDTR(False) #Stop board from resetting
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
        finally:
            try:
                ser.close()
            except Exception:
                pass
    
    #INTERCEPTOR IC's
    def build_interceptor(self):
        #GRAB SPEED FROM USER
        Vi = get_float("Enter an interceptor speed (m/s): ")
        while Vi <= 0:
            Vi = get_float("Speed must be non-negative. Re-enter: ")
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
        print("4. Recorded (from camera tracking log)")

        #PICK MOTION CHOICE
        motion_type = input("Enter choice (1-4): ").strip()
        if motion_type == "1":
            target_motion = "constant_velocity"
        elif motion_type == '2':
            target_motion = "constant_acceleration"
        elif motion_type == '3':
            target_motion = 'weaving'
        elif motion_type == '4':
            target_motion = "recorded"
        else:
            print("Invalid choice, defaulting to constant velocity")
            target_motion = "constant_velocity"

        #IF RECORDED GET DATA FROM LOG
        if target_motion == 'recorded':
            #GET DATA
            records = record_target_motion()

            #EXTRACT DATA INTO LISTS
            timestamps = [r['timestamp'] for r in records]
            az_list = [r['angle_x'] for r in records]
            el_list = [r['angle_y'] for r in records]
            range_list = [r['range_m'] for r in records]

            #STOP THE HUGE JUMPS BY TAKING THE MEDIAN
            def _median_filter(values, window=5):
                #GRAB VALUES AND RETURN MEDIANS
                values = np.array(values, dtype=float)
                n = len(values)
                half = window//2
                return[float(np.median(values[max(0, i-half):min(n, i+half+1)])) for i in range(n)]

            range_list = _median_filter(range_list, window=5)

            #GET FRAME GAPS
            frame_gaps = np.diff(timestamps)
            real_frame_interval = float(np.median(frame_gaps))
            
            #USE DATA AND GET RANGES/TIMES
            initial_range_m = get_float("Enter simulated starting engagement range (m), real range curve will be scaled to start here: ")
            time_scale = get_float("Enter time-scale factor (1.0 = as-recorded): ")

            #STORE TIME STRETCH
            settings.recorded_lookahead = real_frame_interval*time_scale

            trajectory = RecordedTrajectory(timestamps, az_list, el_list, range_list, initial_range_m = initial_range_m, time_scale = time_scale)

            #STORE AND RETURN DATA
            settings.target_motion = target_motion
            return {
                "initial_position" : trajectory.position(0.0).tolist(),
                "initial_velocity" : trajectory.velocity(0.0).tolist(),
                "motion_model" : target_motion,
                "params" : {"trajectory" : trajectory}
            }

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
        #GRAB POSITION INPUTS
        rt0x = get_float("Enter target initial X position(m): ")
        rt0y = get_float("Enter target initial Y position(m): ")
        rt0z = get_float("Enter target initial Z position(m): ")

        rt0 = [float(rt0x), float(rt0y), float(rt0z)] #TARGET STARTING POSITION
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

        #SAVE AND RETURN ALL TARGET IC'S AND MOTION MODEL INFO
        settings.target_motion = target_motion
        return {
            "initial_position": rt0,
            "initial_velocity": vt0,
            "motion_model": target_motion,
            "params": params
        }

    #BUILD RANDOM IC's FOR MONTE CARLO SIMULATION
    #RNG HERE IS NOT RANGE! IT STAND FOR RANDOM NUMBER GENERATOR, WHICH HAS SEEDS FOR REPEATIBILITY
    @staticmethod
    def build_random_ic(rng, overrides = None):
        #NORMALIZE TO EMPTY DICT SO DON'T NEED AS MANY NONE CHECKS
        if overrides is None:
            overrides = {}
        
        #TARGET WITH RANDOM RANGE, POSITION, AND HEADING
        if "R_target" in overrides:
            R_target = overrides["R_target"]
        else:
            R_target = rng.uniform(500.0,3000.0)
        yaw_t = rng.uniform(-np.pi, np.pi)
        pitch_t = rng.uniform(-np.pi/6,np.pi/6)
        rt0 = [
            R_target * np.cos(pitch_t) * np.cos(yaw_t),
            R_target * np.cos(pitch_t) * np.sin(yaw_t),
            R_target * np.sin(pitch_t)
        ]

        #INTERCEPTOR AT ORIGIN WITH RANDOM SPEED AND POINTING AT TARGET WITH DEVIATION
        if "Vi" in overrides:
            Vi = overrides["Vi"]
        else:
            Vi = rng.uniform(150.0,400.0)
        #POINTING ERROR VALUE
        pointing_error_rad = np.radians(overrides.get("pointing_error_deg", 20.0))
        los_yaw = np.arctan2(rt0[1], rt0[0])
        los_pitch = np.arctan2(rt0[2], np.sqrt(rt0[0]**2+rt0[1]**2))
        yaw_i = los_yaw + rng.uniform(-pointing_error_rad, pointing_error_rad)
        pitch_i = los_pitch + rng.uniform(-pointing_error_rad, pointing_error_rad)
        ri0 = [0,0,0]
        vi0 = [
            Vi * np.cos(pitch_i) * np.cos(yaw_i),
            Vi * np.cos(pitch_i) * np.sin(yaw_i),
            Vi * np.sin(pitch_i)
        ]

        #TARGET VELOCITY
        Vt = rng.uniform(50.0,200.0)
        yaw_tv = yaw_t + np.pi + rng.uniform(-np.pi/4,np.pi/4)
        pitch_tv = -pitch_t + rng.uniform(-.2,.2)
        vt0 = [
            Vt * np.cos(pitch_tv) * np.cos(yaw_tv),
            Vt * np.cos(pitch_tv) * np.sin(yaw_tv),
            Vt * np.sin(pitch_tv)
        ]

        #SEVERITY MULTIPLIER
        severity_mult = overrides.get("severity_mult", 1.0)
        #TARGET MOTION MODEL, HALF WEAVING AND EVEN SPLIT BETWEEN CV/CA
        motion_roll = rng.uniform(0.0,1.0)
        if motion_roll < .25:
            motion_type = "constant_velocity"
            params = {}
        elif motion_roll <.5:
            motion_type = "constant_acceleration"
            a_mag = rng.uniform(20.0,60.0) * severity_mult
            a_dir = rng.standard_normal(3)
            a_dir /= np.linalg.norm(a_dir) #UNIT VECTOR
            params = {"accel": (a_mag*a_dir).tolist()}
        else:
            motion_type = "weaving"
            params = {
                "amplitude": rng.uniform(20.0,79.0) * severity_mult,
                "omega": rng.uniform(.5,3.0),
                "axis": rng.choice(["x", "y", "z"])
            }
        
        #RETURN PACKAGE OF ALL INFO IN LIBRARY
        return {
            "ri0": ri0,
            "vi0": vi0,
            "target_data": {
                "initial_position": rt0,
                "initial_velocity": vt0,
                "motion_model": motion_type,
                "params": params
            }
        }
