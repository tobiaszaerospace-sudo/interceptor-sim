#PREDICT WHERE THE MISSILE WILL BE IN THE FUTURE
import numpy as np

class Prediction:
    #INITIALIZE BASED ON YOLO DETECTION FRAMES AND TIME STEP BETWEEN THEM(WHICH OUTPUTS CX,CY,W,H,CONFIDENCE,VALIDITY) TO THEN PREDICT FUTURE POSITION OF TARGET
    def __init__(self, frame_1, frame_2, frame_3, time_step):
        self.frame_1 = frame_1
        self.frame_2 = frame_2
        self.frame_3 = frame_3
        self.time_step = time_step

    #GRAB PAST THREE FRAMES OF POSITION DATA
    def get_position_data(self):
        positions = []
        for frame in [self.frame_1, self.frame_2, self.frame_3]:
            if frame["valid"]:
                positions.append(np.array([frame["cx"], frame["cy"]]))
            else:
                positions.append(None) #HANDLE INVALID FRAMES AS NONE
        return positions
    
    #BASED ON DIFFERENCE IN POSITION DATA, FIND VELOCITY AND ACCELERATION IN X AND Y DIRECTION RESPECTIVELY
    def compute_velocity_acceleration(self, positions):
        #IF ANY POSITION IS NONE, RETURN ZERO VELOCITY AND ACCELERATION
        if None in positions:
            return np.array([0.0, 0.0]), np.array([0.0, 0.0])
        
        #COMPUTE VELOCITY AS DIFFERENCE IN POSITION OVER TIME STEP FOR X AND Y DIRECTION
        vx = (positions[2][0] - positions[1][0]) / self.time_step
        vy = (positions[2][1] - positions[1][1]) / self

        #COMPUTE ACCELERATION AS DIFFERENCE IN VELOCITY OVER TIME STEP
        ax = (vx - (positions[1][0] - positions[0][0]) / self.time_step) / self.time_step
        ay = (vy - (positions[1][1] - positions[0][1]) / self.time_step) / self.time_step

        return np.array([vx, vy]), np.array([ax, ay])

    #PREDICT FUTURE POSITION BASED ON VELOCITY AND ACCELERATION FOR X AND Y DIRECTION TO FEED INTO LOS COMPUTATION FILE
    def predict_future_position(self, velocity, acceleration, future_time):
        #PREDICT FUTURE POSITION USING KINEMATIC EQUATION: s = ut + 0.5at^2
        future_x = self.frame_3["cx"] + velocity[0] * future_time + 0.5 * acceleration[0] * future_time**2
        future_y = self.frame_3["cy"] + velocity[1] * future_time + 0.5 * acceleration[1] * future_time**2

        return {"future_cx": future_x,
                "future_cy": future_y}