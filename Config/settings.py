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
        self.serial_port = "COM4"
        self.baudrate = 115200
        #MODEL SETTINGS
        self.yolo_model_path = "yolov8n.pt"
        #SIMULATION SETTINGS
        self.dt = .01
        self.t_max = 30
        self.kill_radius = 5    #METERS
        self.guidance_mode = "PN"
        self.target_motion = "constant_velocity"
        self.debug = False
        self.plot_interval_ms = 30
        #GUIDANCE SETTINGS
        self.N = 3.0
        self.N_zem = 3.0
        self.max_accel = 150.0
        self.tau = .05
        self.div_count = 10
        #PLOTTING SETTINGS
        self.export_video = True
        self.video_filename = "intercept_simulation.mp4"
        self.plot_export_fps = 30

settings = Settings()