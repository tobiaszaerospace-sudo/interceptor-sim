#GRAB CSV FROM TRACKER AND TURN IT INTO 3D TRAJECTORY FOR MOTION MODEL

#IMPORTS
import csv
import numpy as np
from scipy.interpolate import CubicSpline

#LOAD CSV AND BUILD ANGLES
class RecordedTrajectory:
    #INITIALIZE
    def __init__(self, timestamps, az_deg, el_deg, range_raw_m, initial_range_m = 1000.0, time_scale = 1.0):
        #CHECK FOR LOW TIMESTAMPS
        if len(timestamps) < 4:
            raise ValueError("Need at least 4 recorded rows to build a spline")

        #PUT DATA INTO ARRAY AND START AT T=0
        timestamps = np.array(timestamps, dtype = float)
        timestamps -= timestamps[0]
        timestamps *= time_scale

        az_rad = np.radians(az_deg)
        el_rad = np.radians(el_deg)
        range_raw = np.array(range_raw_m, dtype = float)

        #CHECK FOR NEGATIVE/BAD RANGES
        if range_raw[0] <= 0:
            raise ValueError ("Range at t=0 must be positive to scale from")

        #SCALE RANGE
        self._range_scale = initial_range_m / range_raw[0]
        range_scaled = range_raw * self._range_scale

        #SMOOTH SPLINE OVER ANGLE 
        self.az_spline = CubicSpline(timestamps, az_rad)
        self.el_spline = CubicSpline(timestamps, el_rad)
        self.range_spline = CubicSpline(timestamps, range_scaled)
        self.az_rate_spline = self.az_spline.derivative(1)
        self.el_rate_spline = self.el_spline.derivative(1)
        self.range_rate_spline = self.range_spline.derivative(1)

        #SET MIN MAX AND RANGE
        self.t_min = timestamps[0]
        self.t_max = timestamps[-1]

    #MAKE SURE TO STOP EXTRAPOLATING OUTSIDE RECORDED WINDOW
    def _clamp(self, t):
        return min(max(t, self.t_min), self.t_max)

    #UNIT LOS VECTOR DIRECTION
    def _unit_vector(self, az, el):
        return np.array([
            np.cos(el) * np.cos(az),
            np.cos(el) * np.sin(az),
            np.sin(el)
        ])

    #GET 3D POSITION AT SIM TIME T
    def position(self, t):
        t = self._clamp(t)
        az = self.az_spline(t)
        el = self.el_spline(t)
        R = self.range_spline(t)
        return R * self._unit_vector(az, el)

    #3D VELOCITY AT SIM TIME T
    def velocity(self, t):
        #SET TIME AND GRAB DATA
        t = self._clamp(t)
        az = self.az_spline(t)
        el = self.el_spline(t)
        az_dot = self.az_rate_spline(t)
        el_dot = self.el_rate_spline(t)
        R = self.range_spline(t)
        R_dot = self.range_rate_spline(t)

        u = self._unit_vector(az, el)

        #RATE OF CHANGE FOR UNIT VECTOR
        u_dot = np.array([
            -np.sin(el) * el_dot * np.cos(az) - np.cos(el) * np.sin(az) * az_dot,
            -np.sin(el) * el_dot * np.sin(az) + np.cos(el) * np.cos(az) * az_dot,
             np.cos(el) * el_dot,
        ])
 
        return R_dot * u + R*u_dot

    #3D ACCELERATION VALUE, DOING SMALL RANGE VALUES SO ITS NOT CRAZY VALUES
    def acceleration(self, t, eps=1e-3):
        t = self._clamp(t)
        t_lo = self._clamp(t-eps)
        t_hi = self._clamp(t+eps)
        return (self.velocity(t_hi) - self.velocity(t_lo)) / (t_hi - t_lo)