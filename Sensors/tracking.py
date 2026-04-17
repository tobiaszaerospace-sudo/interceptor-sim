#PURPOSE IS TO CONVERT CAMERA DATA INTO USABLE LOS DATA FROM YOLO AND CHECK ACCURACY VIA APRILTAGS

#IMPORT CAMERA DATA
from Sensors.camera import Camera
#IMPORT YOLO
from ultralytics import YOLO
#IMPORT APRILTAGS
from pupil_apriltags import Detector

#DEFINE TRACKING CLASS FOR CLEAN CODE IN MAIN.PY
class Tracker:
    #INITIALIZE THE TRACKER CLASS
    def __init__(self):
        #SET AS PROPERTY
        #  OF CAMERA SO IT CAN BE REFERENCED EASIER
        self.camera = Camera()
        self.yolo = YOLO("yolov8n.pt") #LOAD YOLO MODEL (CHANGE TO CUSTOM MODEL AFTER TRAINED)
        self.apriltag = Detector()#TODO)FILL IN APRILTAG DETECTOR PARAMETERS

    #STANDARD EMPTY DETECTION RETURN DICTIONARY
    def _empty_detection(self):
        return {"cx": None,      #(x,y) PIXEL COORDINATES
                "cy": None,      #(x,y) PIXEL COORDINATES
                "w": None,       #WIDTH IN PIXELS
                "h": None,       #HEIGHT IN PIXELS
                "confidence": 0.0,  #0.0 TO 1.0
                "valid": False,     #TRUE IF DETECTION SUCCEEDED
                "raw": None,         #RAW OUTPUT FROM DETECTOR FOR DEBUGGING
                }

    #FUNCTION FOR YOLO DETECTION
    def detect_yolo(self, frame):
        detection = self._empty_detection()

        #RUN YOLO ON THE FRAME(SET TO HUMAN CLASS ONLY FOR NOW UNTIL DRONE TRAINING STARTS)
        results = self.yolo(frame, classes = [0], verbose = False) #RUN YOLO, SUPPRESS OUTPUT

        #CHECK AND SEE IF YOLO DIDN'T DETECT ANYTHING
        if len(results) == 0 or len(results[0].boxes) == 0:
            return detection
        
        #USE HIGHEST CONFIDENCE DETECTION
        best_box = results[0].boxes[0]
        #GRAB THE OUTPUT TENSOR FROM YOLO
        output_tensor = best_box.xywhc[0] #GET (x_center, y_center, width, height, confidence)
        #CONVERT THE OUTPUT TENSOR TO MY VARIABLES IN A LIBRARY
        yolo_output_vals = {
            "cx": float(output_tensor[0]), #X CENTER
            "cy": float(output_tensor[1]), #Y CENTER
            "w": float(output_tensor[2]),  #WIDTH
            "h": float(output_tensor[3]),  #HEIGHT
            "confidence": float(output_tensor[4]), #CONFIDENCE
            "valid": True, #VALID DETECTION
            "raw": output_tensor #STORE RAW OUTPUT FOR DEBUGGING
        }
        return yolo_output_vals 
    
    #FUNCTION FOR APRILTAG DETECTION(BASELINE)
    def detect_apriltag(self, frame):
        detection = self._empty_detection()
        #TODO) RUN APRILTAG, FILL PIXEL, CONFIDENCE, AND VALID
        return detection #WILL MODIFY EMPTY DETECTION WITH VALEUS AND RETURN THAT

    #RETREIVE FRAME FROM CAMERA AND RUN DETECTION/TRACKING ON IT
    def process_frame(self):
        #1) GRAB A CAMERA FRAME
        frame = self.camera.read()
        #2) RUN DETECTIONS FOR EVERYTHING
        det_yolo = self.detect_yolo(frame)
        det_tag = self.detect_apriltag(frame) #(Treat this as 100% accuracy to then compare other methods to)

        #RETURN VALUES
        return {
            "yolo": det_yolo, #YOLO DETECTION OUTPUT DICTIONARY
            "apriltag": det_tag, #APRILTAG DETECTION OUTPUT DICTIONARY
            "frame": frame #RETURN THE FRAME FOR DEBUGGING PURPOSES
        }
    #RELEASE ALL RESOURCES USED BY TRACKER
    def release(self):
        self.camera.release()
