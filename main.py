#IMPORT LIBRARIES
import time
import cv2
import numpy as np
#IMPORT CLASSES
from Sensors.camera import Camera
from Sensors.tracking import Tracker
from Detection_Data_Processing.prediction import Prediction
from Detection_Data_Processing.los_computation import LOSComputer
from Hardware.servo import ServoController
from Config.settings import Settings

#MAKE OPTION FUNCTIONS
#OPTION 1: TRACKING
def run_gimbal_tracking():
    settings = Settings()
    print("Starting Gimbal Tracking...")
    #INITIALIZE CLASSES
    tracker = Tracker()
    servo = ServoController(port = settings.servo_port, buad = settings.servo_baud)
