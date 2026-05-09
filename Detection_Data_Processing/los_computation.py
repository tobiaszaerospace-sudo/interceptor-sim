#TURNS PIXEL COORDINATES INTO LOS ANGLES

#IMPORT MATH
import math
#MAKE CLASS FOR LOS COMPUTATION
class LOSComputer: 
    #INITIALIZE
    def __init__(self, camera_fov_degrees, image_width, image_height):
        self.camera_fov_degrees = camera_fov_degrees
        self.image_width = image_width
        self.image_height = image_height

        #COMPUTE VERTICAL FOV BASED ON ASPECT RATIO
        aspect_ratio = image_height / image_width
        self.camera_fov_degrees_y = 2*math.degrees(math.atan(aspect_ratio*math.tan(math.radians(camera_fov_degrees)/2)))
        #PRECOMPUTE PIXEL TO DEGREE SCALE FOR X AND Y
        self.deg_per_pixel_x = self.camera_fov_degrees / image_width
        self.deg_per_pixel_y = self.camera_fov_degrees_y / image_height

    #COMPUTE LOS ANGLES FROM PIXEL COORDINATES
    def compute_los_angles(self, pixel_x, pixel_y):
        #CALCULATE DEGREE OFFSETS FROM IMAGE CENTER
        offset_x = pixel_x - (self.image_width / 2)
        offset_y = pixel_y - (self.image_height / 2)

        #CONVERT OFFSETS TO ANGLES
        angle_x = offset_x * self.deg_per_pixel_x
        angle_y = offset_y * self.deg_per_pixel_y

        return {"angle_x": angle_x,
                 "angle_y": angle_y
                 }
    