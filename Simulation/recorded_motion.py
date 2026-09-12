#GRAB CSV FROM TRACKER AND TURN IT INTO 3D TRAJECTORY FOR MOTION MODEL

#IMPORTS
import csv
import numpy as np
from scipy.interpolate import CubicSpline

#LOAD CSV AND BUILD ANGLES
class RecordedTrajectory:
    #INITIALIZE
    def __init__(self, csv_path, range_m = 1000.0, time_scale = 1.0):
        timestamps = []
        az_list = []
        el_list = []

        #READ LOGGED ROWS
        with open(csv_path, newline = "") as f:
            reader = csv.DictReader(f)
            for row in reader:
                timestamps.append(float(row['timestamp']))
                az_list.append(float(row['angle_x']))
                el_list.append(float(row['angle_y']))

        #CHECK FOR MIN LOGS
        if len(timestamps) < 4:
            raise ValueError("Need at least 4 recorded rows to build a spline")

        #PUT DATA INTO ARRAY AND START AT T=0
        timestamps = np.array(timestamps)
        timestamps -= timestamps[0]
        timestamps *= time_scale

        az_rad = np.radians(az_list)
        el_rad = np.radians(el_list)

        #SMOOTH SPLINE OVER ANGLE 
        self.az_spline = CubicSpline(timestamps, az_rad)
        self.el_spline = CubicSpline(timestamps, el_rad)
        self.az_rate_spline = self.az_spline.derivative(1)
        self.el_rate_spline = self.el_spline.derivative(1)

        #SET MIN MAX AND RANGE
        self.t_min = timestamps[0]
        self.t_max = timestamps[-1]
        self.R = range_m

    #MAKE SURE TO STOP EXTRAPOLATING OUTSIDE RECORDED WINDOW
    def _clamp(self, t):
        return min(max(t, self.t_min), self.t_max)

    #GET 3D POSITION AT SIM TIME T
    def position(self, t):
        t = self._clamp(t)
        az = self.az_spline(t)
        el = self.el_spline(t)
        return self.R * np.array([
            np.cos(el) * np.cos(az),
            np.cos(el) * np.sin(az),
            np.sin(el)
        ])

    #3D VELOCITY AT SIM TIME T
    def velocity(self, t):
        #SET TIME AND GRAB DATA
        t = self._clamp(t)
        az = self.az_spline(t)
        el = self.el_spline(t)
        az_dot = self.az_rate_spline(t)
        el_dot = self.el_rate_spline(t)

        #CONVERT TO CARTESIAN
        dx = -np.sin(el) * el_dot * np.cos(az) - np.cos(el) * np.sin(az) * az_dot
        dy = -np.sin(el) * el_dot * np.sin(az) + np.cos(el) * np.cos(az) * az_dot
        dz = np.cos(el) * el_dot
 
        return self.R * np.array([dx, dy, dz])

    #3D ACCELERATION VALUE, DOING SMALL RANGE VALUES SO ITS NOT CRAZY VALUES
    def acceleration(self, t, eps=1e-3):
        t = self._clamp(t)
        t_lo = self._clamp(t-eps)
        t_hi = self._clamp(t+eps)
        return (self.velocity(t_hi) - self.velocity(t_lo)) / (t_hi - t_lo)