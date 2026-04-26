#PURPOSE IS TO CONVERT CAMERA DATA INTO USABLE LOS DATA FROM YOLO AND CHECK ACCURACY VIA APRILTAGS

#IMPORT CAMERA DATA
from Sensors.camera import Camera
#IMPORT YOLO
from ultralytics import YOLO
#IMPORT OPENCV FOR IMAGE PROCESSING
import cv2
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
        self.apriltag = Detector(families=["tag36h11"], nthreads=4,quad_decimate=1.0,quad_sigma=0.0, refine_edges=True,)

    #STANDARD EMPTY DETECTION RETURN DICTIONARY
    def _empty_detection(self):
        return {"cx": None,      #x PIXEL COORDINATE
                "cy": None,      #y PIXEL COORDINATE
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

        #CONVERT TO GRAYSCALE FOR APRILTAG DETECTION
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        #RUN THE DETECTOR
        tags = self.apriltag.detect(gray_frame, estimate_tag_pose=False, camera_params=[None], tag_size=None)

        #IN EVENT OF NO DETECTION
        if len(tags) == 0:
            return detection
        
        #USE THE FIRST DETECTED TAG (ONLY GONNA BE USING ONE ANYWAYS)
        tag = tags[0]

        #GRAB THE CENTER AND SIZE OF THE DETECTED TAG
        cx, cy = tag.center
        w, h = tag.size

        #RETURN DICTIONARY FORMAT
        return {
            "cx": float(cx),    #X CENTER
            "cy": float(cy),    #Y CENTER
            "w": float(w),      #WIDTH
            "h": float(h),      #HEIGHT
            "confidence": 1.0,  #ASSUME 100% CONFIDENCE FOR APRILTAG
            "valid": True,      #VALID DETECTION
            "raw": tags         #STORE RAW OUTPUT FOR DEBUGGING
        }

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
