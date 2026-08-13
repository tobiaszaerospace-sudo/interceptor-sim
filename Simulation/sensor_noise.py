#SENSOR NOISE MODEL FOR LOS ANGLE MEASUREMENTS
#IMPORT LIBRARIES
import numpy as np
import math

#BLOCK SERIAL IMPORT SO IT DOESN'T CRASH IF PYSERIAL ISN'T INSTALLED
try:
    import serial
except ImportError:
    serial = None

#MAKE CLASS FOR NOISY LOS ANGLE MEASUREMENTS FROM TRUE RELATIVE POSITION
#FALSE IS FOR SYNTHETIC GUSSIAN NOISE
#TRUE IS FOR REAL IMU DATA READ FROM ARDUINO SERIAL
class SensorNoise:
    #INITIALIZE THE SETTINGS 
    def __init__(self, settings, rng_seed = None, shared_ser = None):
        self.settings = settings
        #SEEDED RNG FOR REPRODUCIBILITY IN MONTE CARLO
        self.rng = np.random.default_rng(rng_seed)
        self._ser = None

        #TRACK WHETHER CONNECTION IS OPENED
        self._owns_connection = False

        #IF A SHARED CONNECTION IS PASSED IN USE THAT INSTEAD OF OPENING SECOND
        if shared_ser is not None:
            self._ser = shared_ser
        
        #OTHERWISE IF REAL IMU DATA REQUESTED USE THAT
        if settings.use_imu:
            self._open_serial()
        
    #OPEN SERIAL CONNECTION TO ARDUINO IMU SKETCH
    def _open_serial(self):
        #IF SERIAL ISN'T RECOGNIZED, FALLBACK TO THE FAKE NOISE
        if serial is None:
            print('Pyserial not installed. Falling back to synthetic noise')
            self.settings.use_imu = False
            return
        #IF SERIAL IS THERE, GO AHEAD AND OPEN IT UP
        try:
            self._ser = serial.Serial(self.settings.imu_port, self.settings.imu_baud, timeout = .05)
            self._owns_connection = True
            import time
            time.sleep(2)
            print(f"IMU serial connected on {self.settings.imu_port}")
        except Exception as e:
            #IF THERES A BREAK, SAY SO AND FALLBACK TO SYNTHETIC
            print(f"IMU serial failed: {e}. Falling back to synthetic noise")
            self.settings.use_imu = False
            self._ser = None
    
    #COMPUTE AZIMUTH AND ELEVATION FROM RELATIVE POSITION VECTOR
    def _true_angles(self, r_rel):
        Range = np.linalg.norm(r_rel)
        if Range < 1e-6:
            return 0.0,0.0,False
        az = math.atan2(r_rel[1], r_rel[0])
        el = math.asin(float(np.clip(r_rel[2]/Range, -1.0, 1.0)))
        return az, el, True
    
    #MAKE SYNTHETIC NOISE ANGLE MEASUREMENT FROM TRUE R_REL
    def _synthetic_measurement(self, r_rel):
        #GET TRUE ANGLES
        az_true, el_true, valid = self._true_angles(r_rel)
        if not valid:
            return {
                "valid" :   False,
                "az_meas" : 0.0,
                "el_meas" : 0.0,
                "az_true" : 0.0,
                el_true   : 0.0,
            }
        #CONVERT SENSOR NOISE PARAMETERS FROM DEGREES TO RADIANS
        az_sigma = math.radians(self.settings.sensor_az_sigma)
        el_sigma = math.radians(self.settings.sensor_el_sigma)
        az_bias  = math.radians(self.settings.sensor_az_bias)
        el_bias  = math.radians(self.settings.sensor_el_bias)

        #ADD BIAS PLUG NOISE TO TRUE ANGLES
        az_meas = az_true + az_bias + self.rng.normal(0.0, az_sigma)
        el_meas = el_true + el_bias + self.rng.normal(0.0, el_sigma)

        return {
            "valid"  : True,
            "az_meas": az_meas,
            "el_meas": el_meas,
            "az_true": az_true,
            "el_true": el_true,
        }
    
    #GENERATE SYNTHETIC NOISY ANGLE MEASUREMENT FROM TRUE R_REL
    def _imu_measurement(self, r_rel):
        #CHECK IF EVERYTHINGS OPEN
        if self._ser is None or not self._ser.is_open:
            return self._synthetic_measurement(r_rel)
        
        #FLUSH STALE DATA, READ UNTIL BUFFER IS CURRENT
        try:
            self._ser.reset_input_buffer()
            line = self._ser.readline().decode('utf-8').strip()
            parts = line.split(",")
            if len(parts) != 2:
                raise ValueError(f"Unexpected format: {line}")
            
            az_meas = math.radians(float(parts[0]))
            el_meas = math.radians(float(parts[1]))

            #STILL COMPUTE TRUE ANGLES FOR LOGGING/VALIDATION
            az_true, el_true, valid = self._true_angles(r_rel)

            return {
                "valid"  : True,
                "az_meas": az_meas,
                "el_meas": el_meas,
                "az_true": az_true,
                "el_true": el_true,
            }
        except Exception as e:
            if self.settings.debug:
                print(f"IMU read error: {e}. Using synthetic fallback.")
            return self._synthetic_measurement(r_rel)
    
    #MEASURE RETURNS MEASUREMENT DICT REGARDLESS OF MODE
    def measure(self, r_rel):
        #CHECK IF THEY WANT IMU OR SYNTHETIC
        if self.settings.use_imu:
            return self._imu_measurement(r_rel)
        else:
            return self._synthetic_measurement(r_rel)
        
    #CLOSE ALL SERIAL PORTS
    def close(self):
        if self._ser and self._ser is not None and self._ser.is_open:
            self._ser.close()