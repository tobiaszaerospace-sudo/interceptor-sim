#PURPOSE IS TO CONVERT CAMERA DATA INTO USABLE LOS DATA FROM YOLO AND CHECK ACCURACY VIA APRILTAGS

#IMPORT CAMERA DATA
from Sensors.camera import Camera
#IMPORT YOLO

#IMPORT APRILTAGS
from pupil_apriltags import Detector

#DEFINE TRACKING CLASS FOR CLEAN CODE IN MAIN.PY
class Tracker:
    #INITIALIZE THE TRACKER CLASS
    def __init__(self):
        #SET AS PROPERTY OF CAMERA SO IT CAN BE REFERENCED EASIER
        self.camera = Camera()
        
    #STANDARD EMPTY DETECTION RETURN DICTIONARY
    def _empty_detection(self):
        return {"pixel": None,      #(x,y) PIXEL COORDINATES
                "confidence": 0.0,  #0.0 TO 1.0
                "valid": False,     #TRUE IF DETECTION SUCCEEDED
                "los": {
                    "angle": None,  #WILL BE FILLED IN LATER
                    "rate": None,   #WILL BE FILLED IN LATER
                }
            }

    
    #FUNCTION FOR YOLO DETECTION
    def detect_yolo(self, frame):
        
        detection = self._empty_detection()
        #TODO) RUN YOLO, FILL PIXEL, CONFIDENCE, AND VALID
        return detection #WILL MODIFY EMPTY DETECTION WITH VALEUS AND RETURN THAT
    
    #FUNCTION FOR APRILTAG DETECTION(BASELINE)
    def detect_apriltag(self, frame):
        detection = self._empty_detection()
        #TODO) RUN APRILTAG, FILL PIXEL, CONFIDENCE, AND VALID
        return detection #WILL MODIFY EMPTY DETECTION WITH VALEUS AND RETURN THAT
    
    #CONVERT PIXEL COORDINATES INTO LOS ANGLE AND RATE
    def compute_los(self, pixel_cords):
        if pixel_cords == None:
            return {"angle": None, "rate": None}
        #TODO) LOS MATH
        return {"angle": 0.0, "rate": 0.0} #WILL BE RETURNING LOS ANGLE AND RATE DICTIONARY, WHICH WILL LATER ADD TO ORIGINAL DICTIONARY IN PROCESS_FRAME
    
    #DETERMINE ACCURACY BASED ON APRILTAG MEASUREMENT
    def compute_accuracy(self, apriltag_los, method_los):
        #IF APRILTAG DOESN'T RETURN ANYTHING, DON'T COMPUTE ACCURACY
        if apriltag_los is None or method_los is None:
            return None
        error = abs(method_los - apriltag_los)
        return 1-(error/abs(apriltag_los))
        #PLACEHOLDER: WILL BE REPLACED WHEN LOS RETURNS A DICTIONARY

    #FUNCTION FOR CONVERTING PIXEL COORDINATES INTO LOS 

    #RETREIVE FRAME FROM CAMERA AND RUN DETECTION/TRACKING ON IT
    def process_frame(self):
        #1) GRAB A CAMERA FRAME
        frame = self.camera.read()
        #2) RUN DETECTIONS FOR EVERYTHING
        det_yolo = self.detect_yolo(frame)
        det_tag = self.detect_apriltag(frame) #(Treat this as 100% accuracy to then compare other methods to)

        #3) DO LOS CONVERSION FOR EACH ONE AND INSERT INTO DETECTOR DICTIONARY

        #3B) DO YOLO LOS CONVERSION - THEN ADD TO DETECTOR DICTIONARY

        #3C) DO APRILTAG LOS CONVERSION - THEN ADD TO DETECTOR DICTIONARY

        #4) DO ACCURACY(RELATIVE TO APRILTAG)

        #4B) DO YOLO ACCURACY

        #RETURN VALUES
        return None #WILL BE LOS, RAW DETECTOR OUTPUTS, ACCURACY METRICS, DEBUG INFO
    #RELEASE ALL RESOURCES USED BY TRACKER
    def release(self):
        self.camera.release()

    
    




