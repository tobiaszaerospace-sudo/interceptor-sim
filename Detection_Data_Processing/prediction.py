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
        vy = (positions[2][1] - positions[1][1]) / self.time_step

        #COMPUTE ACCELERATION AS DIFFERENCE IN VELOCITY OVER TIME STEP
        ax = (vx - (positions[1][0] - positions[0][0]) / self.time_step) / self.time_step
        ay = (vy - (positions[1][1] - positions[0][1]) / self.time_step) / self.time_step

        return np.array([vx, vy]), np.array([ax, ay])

    #ZEROETH ORDER PREDICTION: ASSUME VELOCITY AND ACCELERATION ARE ZERO, SO FUTURE POSITION IS SAME AS CURRENT POSITION
    def zeroeth_order_prediction(self):
        return {"future_cx": self.frame_3["cx"],
                "future_cy": self.frame_3["cy"]}
    
    #FIRST ORDER PREDICTION: ASSUME ACCELERATION IS ZERO, SO FUTURE POSITION IS BASED ON CURRENT VELOCITY
    def first_order_prediction(self, velocity, future_time):
        future_x = self.frame_3["cx"] + velocity[0] * future_time
        future_y = self.frame_3["cy"] + velocity[1] * future_time

        return {"future_cx": future_x,
                "future_cy": future_y}
    #PREDICTION BASED ON CURRENT VELOCITY AND ACCELERATION, USING KINEMATIC EQUATIONS TO PREDICT FUTURE POSITION
    def second_order_prediction(self, velocity, acceleration, future_time):
        future_x = self.frame_3["cx"] + velocity[0] * future_time + 0.5 * acceleration[0] * future_time**2
        future_y = self.frame_3["cy"] + velocity[1] * future_time + 0.5 * acceleration[1] * future_time**2

        return {"future_cx": future_x,
                "future_cy": future_y}
    
    #ADAPTIVE MODEL FOR SIMPLER COMPUTATION BASED ON HIGH/LOW ACCELERATION VALUES
    def adaptive_prediction(self, velocity, acceleration, future_time, accel_threshold=5.0):
        #IF ACCELERATION IS SMALL, USE FIRST ORDER PREDICTION
        if abs(acceleration[0]) < accel_threshold and abs(acceleration[1]) < accel_threshold:
            return self.first_order_prediction(velocity, future_time)
        #OTHERWISE, USE SECOND ORDER PREDICTION
        else:
            return self.second_order_prediction(velocity, acceleration, future_time)