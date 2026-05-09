#SET UP GLOBAL SETTINGS THAT CAN BE CHANGED LATER - MAKES EVERYTHING MORE MODULAR AND FLEXIBLE
class Settings:
    def __init__(self):
        #CAMERA SETTINGS
        self.camera_fov_x = 70.0
        self.image_width = 640
        self.image_height = 480
        self.camera_index = 0
        self.fps = 30
        #HARDWARE SETTINGS
        self.servo_port = "COM4"
        self.servo_baud = 115200
        #MODEL SETTINGS
        self.yolo_model_path = "yolov8n.pt"
settings = Settings()