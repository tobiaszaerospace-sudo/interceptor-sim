#CALCULATE STEREO VISION DEPTH
#IMPORT FUNCTIONS
import math

#SPLIT COMBINED SIDE BY SIDE FRAME INTO LEFT AND RIGHT
def split_frame(frame):
    h, w = frame.shape[:2]
    half = w//2
    return frame[:, :half], frame[:, half:]

#CONVERT HORIZONTAL FOV INTO FOCAL LENGTH IN PIXELS
def focal_length_px(image_width, fov_degrees):
    return (image_width/2) / math.tan(math.radians(fov_degrees)/2)

#TRIANGULATION FORMULA
def estimate_depth(disparity_px, baseline_m, focal_px):
    if disparity_px is None or disparity_px <= 0:
        return None
    return (baseline_m * focal_px) / disparity_px