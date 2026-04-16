#PURPOSE IS TO HANDLE CAMERA INPUT

#IMPORTING OPENCV FOR COMPUTER VISION
import cv2

#DEFINE CAMERA CLASS FOR CLEAN CODE IN MAIN.PY
class Camera:
    #INITIALIZE CAMERA OBJECT
    def __init__(self, device_index=0): 

        #DEFINE CAPTURE PROPERTY, WHICH IS THE ACTUAL IMAGE THAT WAS CAPTURED
        self.capture = cv2.VideoCapture(device_index)

        #VERIFY THE CAMERA WAS ACTUALLY OPENED, STOP ERROR BEFORE IT MAGNIFIES LATER ON IN CODE
        if not self.capture.isOpened():
            raise RuntimeError("Error: Could not open camera.")

    #CAPTURE FRAME FROM CAMERA
    def read(self):
        
        #SEE IF FRAME IS READABLE
        successful, frame = self.capture.read()
        
        #IF IT ISN'T READABLE, RAISE AN ERROR BEFORE IT MAGNIFIES LATER ON IN CODE
        if not successful:
            raise RuntimeError("Error: Failed to read frame from Camera")
        
        #IF IT IS READABLE, RETURN IT TO USER 
        return frame
    
    #RELEASE CAMERA HARDWARE AND CLOSE ANY OPENCV WINDOWS THAT MAY BE OPENED LATER ON
    def release(self):

        self.capture.release()  #LET GO OF CAMERA
        cv2.destroyAllWindows() #CLOSE WINDOW
        