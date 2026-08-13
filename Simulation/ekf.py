#EXTENDED KALMAN FILTER FOR ANGLE ONLY TARGET TRACKING
#ESTIMATES RELATIVE STATE FROM NOSIY LOS ANGLE MEASUREMENTS, FEEDS GUIDANCE LAW WITH ESTIMATE INSTEAD OF TRUE STATE
#IMPORT LIBRARIES
import numpy as np
import math
from Config.settings import settings

#CLASS FOR EKF
class EKF:

    #INITIALIZATIONS
    def __init__(self, dt):
        #TIME STEP 
        self.dt = dt

        #SENSOR NOISE VARIANCE
        az_sigma = math.radians(settings.sensor_az_sigma)
        el_sigma = math.radians(settings.sensor_el_sigma)

        #MEASUREMENT NOISE COVARIANCE MATRIX 2X2, DIAGONAL BECAUSE OF INDEPENDENCE
        self.measurement_noise = np.diag([az_sigma**2, el_sigma**2])

        #STATE UNCERTAINTY MATRIX 6X6, FILTER SHRINKS AUTOMATICALLY WHEN MEASUREMENTS COME IN
        self.state_uncertainty = np.diag([500**2]*3 + [100**2]*3)

        #HOW MUCH TARGET CAN MANEUVER BETWEEN STEPS
        self.target_maneuver_noise = 50.0

        #CURRENT STATE ESTIMATE 
        self.estimated_state = np.zeros(6)
        self.is_initialized = False

    #INITIALIZATION FOR FIRST MEASUREMENT
    def initialize_from_first_measurement(self, az_meas, el_meas):
        #GUESSING AT RANGE, CAN'T FIND FROM ANGLE MEAS ALONE
        range_guess = 1000.0

        #CONVERT SPHERICAL TO CARTESIAN
        rx = range_guess * math.cos(el_meas) * math.cos(az_meas)
        ry = range_guess * math.cos(el_meas) * math.sin(az_meas)
        rz = range_guess * math.sin(el_meas)

        #VELOCITY UNKNOWN AT START
        self.estimated_state = np.array([rx, ry, rz, 0.0, 0.0, 0.0])
        self.is_initialized  = True

    #PREDICTION FUNCTION FOR WHERE WE THINK THE TARGET IS NOW BASED ON LAST STEP
    def predict(self):
        #DON'T PREDICT UNTIL WE HAVE AN INITIAL MEASUREMENT
        if not self.is_initialized:
            return
        
        #TIME STEP
        dt = self.dt

        #STATE TRANSITION MATRIX, CV
        transition = np.eye(6)
        transition[0, 3] = dt
        transition[1, 4] = dt
        transition[2, 5] = dt

        #PROCESS NOISE MATRIX
        q = self.target_maneuver_noise * dt
        process_noise = np.diag([q*(dt**2)/3.0]*3 + [q]*3)

        #PROPAATE STATE ESTIMATE FORWARD A STEP 
        self.estimated_state = transition @ self.estimated_state

        #MOVE THE UNCERTAINTY FORWARD AS WELL
        self.state_uncertainty = (transition@self.state_uncertainty@transition.T + process_noise)

    #PREDICT MEASUREMENT OF WHAT THE IMU WOULD SEE GIVEN OUR ESTIMATE
    def _predicted_angles(self):
        #PREDICTION IN CARTESIAN
        rx = self.estimated_state[0]
        ry = self.estimated_state[1]
        rz = self.estimated_state[2]
        estimated_range = math.sqrt(rx**2 + ry**2 + rz**2)

        #IF THE RANGE IS TOO SMALL, THE AZ AND EL DON'T REALLY MATTER
        if estimated_range < 1e-9:
            return np.zeros(2)
        
        #MATH FOR AZ AND EL FROM RX AND RY AND RZ
        az_predicted = math.atan2(ry, rx)
        el_predicted = math.asin(float(np.clip(rz / estimated_range, -1.0, 1.0)))
        return np.array([az_predicted, el_predicted])
    
    #MEASUREMENT JACOBIAN FOR HOW SENSITIVE ANGLES ARE TO STATE CHANGE
    def _measurement_jacobian(self):
        rx = self.estimated_state[0]
        ry = self.estimated_state[1]
        rz = self.estimated_state[2]

        range_squared     = rx**2 + ry**2 + rz**2
        estimated_range   = math.sqrt(range_squared)
        range_xy_squared  = rx**2 + ry**2
        range_xy          = math.sqrt(max(range_xy_squared, 1e-12))

        #JACOBIAN AS AZ, EL X RX, RY, RZ, VX, VY, VZ
        #ANGLE DOESN'T DEPEND ON VELOCITY
        jacobian = np.zeros((2,6))

        #IN CASE THE RANGE IS TOO SMALL
        if estimated_range < 1e-9:
            return jacobian
        
        #AZIMUTH PARTIAN DERIVATIVES POSITION
        jacobian[0, 0] = -ry / range_xy_squared
        jacobian[0, 1] =  rx / range_xy_squared

        #ELEVATION PARTIAL DERIVATIVES POSITION
        jacobian[1, 0] = -rx * rz / (range_squared * range_xy)
        jacobian[1, 1] = -ry * rz / (range_squared * range_xy)
        jacobian[1, 2] =  range_xy / range_squared

        return jacobian
    
    #UPDATE USING NEW MEASUREMENT
    def update(self, az_meas, el_meas):
        #FIRST MEASUREMENT EVER, INITIALIZED INSTEAD OF UPDATED
        if not self.is_initialized:
            self.initialize_from_first_measurement(az_meas, el_meas)
            return np.zeros(2)
        
        #WHAT TEH SENSOR SAW
        actual_measurement = np.array([az_meas, el_meas])

        #WHAT FILTER EXPECTED TO SEE
        predicted_measurement = self._predicted_angles()

        #INNOVATION - HOW WRONG PREDICTION WAS
        innovation = actual_measurement - predicted_measurement

        #WRAP AZIMUTH INNOVATION TO JUMP ACROSS +- 180
        innovation[0] = (innovation[0] + np.pi) % (2*np.pi)-np.pi

        #JACOBIAN AT CURRENT STATE ESTIMATE
        jacobian = self._measurement_jacobian()

        #INNOVATION COVARIANCE, COMBINING STATE UNCERTAITNY AND SENSOR NOISE
        innovation_cov = (jacobian@self.state_uncertainty@jacobian.T + self.measurement_noise)

        #HOW MUCH TO TRUST MEASUREMENT VS PREDICTION, HIGH GAIN = TRUST MEASUREMENT, LOW GAIN = TRUST PREDICTIN
        kalman_gain = self.state_uncertainty@jacobian.T@np.linalg.inv(innovation_cov)

        #CORRECT STATE ESTIMATE USING INNOVATION
        self.estimated_state = self.estimated_state + kalman_gain @ innovation

        #REDUCE UNCERTAINTY NOW WITH NEW MEASUREMENT
        self.state_uncertainty = ((np.eye(6)-kalman_gain @ jacobian) @ self.state_uncertainty)

        return innovation
    
    #NEES - NORMALIZED ESTIMATION ERROR SQUARED 
    def nees(self, r_rel_true, v_rel_true):
        #IF NOT INITIALIZED, RETURN NOTHING
        if not self.is_initialized:
            return 0.0
        
        #STACK TRUE RELATIVE POSITION AND VELOCITY INTO ONE 6-ELEMENT VECTOR
        true_state = np.concatenate([r_rel_true, v_rel_true])

        #ESTIMATION ERROR
        error = true_state - self.estimated_state

        try:
            #NORMALIZE ERROR BY FILTERS OWN UNCERTAINTY ESTIMATE
            return float(error @ np.linalg.inv(self.state_uncertainty) @ error)
        except np.linalg.LinAlgError:
            #STATE UNCERTAINTY MATRIX IS GIVING NUMERICAL ISSUE, RETURN 0 AS FALLBACK
            return 0.0
    
    #OUTPUTS
    def r_est(self):
        #ESTIMATED RELATIVE POSITION (3,) IN METERS
        return self.estimated_state[0:3].copy()

    def v_est(self):
        #ESTIMATED RELATIVE VELOCITY (3,) IN M/S
        return self.estimated_state[3:6].copy()

    def range_est(self):
        #ESTIMATED RANGE (SCALAR) IN METERS
        return float(np.linalg.norm(self.estimated_state[0:3]))

    #RANGE AND VC NEEDED FOR GUIDANCE WRITING FUNCTIONS
    def range_hat_est(self):
        #ESTIMATES LOS UNIT VECTOR
        r = self.estimated_state[0:3]
        n = np.linalg.norm(r)
        return r/n if n > 1e-6 else np.zeros(3)
    
    def Vc_est(self):
        #ESTIMATION CLOSING VELOCITY 
        r_hat = self.range_hat_est()
        return float(-np.dot(self.estimated_state[3:6], r_hat))