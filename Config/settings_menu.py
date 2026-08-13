from Config.settings import settings

def run_settings_menu():
    while True:
        #SHOW CURRENT SETTINGS TO USER
        print("\n --- SETTINGS MENU --- ")
        print(f"1.  Camera FOV X: {settings.camera_fov_x}")
        print(f"2.  Image Width: {settings.image_width}")
        print(f"3.  Image Height: {settings.image_height}")
        print(f"4.  Camera Index: {settings.camera_index}")
        print(f"5.  FPS: {settings.fps}")
        print(f"6.  Servo Port: {settings.servo_port}")
        print(f"7.  Servo Baud: {settings.servo_baud}")
        print(f"8.  YOLO Model Path: {settings.yolo_model_path}")
        print(f"9.  Simulation dt: {settings.dt}")
        print(f"10. Max Accel: {settings.max_accel}")
        print(f"11. Navigation Constant N: {settings.N}")
        print(f"12. Kill Radius: {settings.kill_radius}")
        print(f"13. Use EKF: {settings.use_ekf}")
        print(f"14. Use Real IMU: {settings.use_imu}")
        print(f"15. Sensor Az Sigma (deg): {settings.sensor_az_sigma}")
        print(f"16. Sensor El Sigma (deg): {settings.sensor_el_sigma}")
        print(f"17. Sensor Az Bias (deg): {settings.sensor_az_bias}")
        print(f"18. Sensor El Bias (deg): {settings.sensor_el_bias}")
        print(f"19. IMU Port: {settings.imu_port}")
        print(f"20. IMU Baud: {settings.imu_baud}")
        print("21. Return to Main Menu")

        choice = input("Enter setting number (1-21): ").strip()
        while choice not in [str(i) for i in range(1, 22)]:
            print("Invalid input.")
            choice = input("Enter setting number (1-21): ").strip()

        if choice == "21":
            print("Returning to Main Menu...")
            break

        #CAMERA FOV
        elif choice == "1":
            try:
                new_fov = float(input("Enter new Camera FOV X in degrees: ").strip())
                settings.camera_fov_x = new_fov
                print(f"Camera FOV X updated to {new_fov} degrees.")
            except ValueError:
                print("Invalid input.")

        #IMAGE WIDTH
        elif choice == "2":
            try:
                new_width = int(input("Enter new Image Width in pixels: ").strip())
                settings.image_width = new_width
                print(f"Image Width updated to {new_width} pixels.")
            except ValueError:
                print("Invalid input.")

        #IMAGE HEIGHT
        elif choice == "3":
            try:
                new_height = int(input("Enter new Image Height in pixels: ").strip())
                settings.image_height = new_height
                print(f"Image Height updated to {new_height} pixels.")
            except ValueError:
                print("Invalid input.")

        #CAMERA INDEX
        elif choice == "4":
            try:
                new_index = int(input("Enter new Camera Index: ").strip())
                settings.camera_index = new_index
                print(f"Camera Index updated to {new_index}.")
            except ValueError:
                print("Invalid input.")

        #FPS
        elif choice == "5":
            try:
                new_fps = int(input("Enter new FPS: ").strip())
                settings.fps = new_fps
                print(f"FPS updated to {new_fps}.")
            except ValueError:
                print("Invalid input.")

        #SERVO PORT
        elif choice == "6":
            new_port = input("Enter new Servo Port (e.g. COM3): ").strip()
            settings.servo_port = new_port
            print(f"Servo Port updated to {new_port}.")

        #SERVO BAUD
        elif choice == "7":
            try:
                new_baud = int(input("Enter new Servo Baud Rate: ").strip())
                settings.servo_baud = new_baud
                print(f"Servo Baud Rate updated to {new_baud}.")
            except ValueError:
                print("Invalid input.")

        #YOLO MODEL PATH
        elif choice == "8":
            new_path = input("Enter new YOLO Model Path: ").strip()
            settings.yolo_model_path = new_path
            print(f"YOLO Model Path updated to {new_path}.")

        #SIMULATION DT
        elif choice == "9":
            try:
                settings.dt = float(input("Enter new dt (e.g. 0.01): ").strip())
                print(f"dt updated to {settings.dt}")
            except ValueError:
                print("Invalid input.")

        #MAX ACCEL
        elif choice == "10":
            try:
                settings.max_accel = float(input("Enter new max accel (m/s^2): ").strip())
                print(f"Max accel updated to {settings.max_accel}")
            except ValueError:
                print("Invalid input.")

        #NAVIGATION CONSTANT
        elif choice == "11":
            try:
                settings.N = float(input("Enter new navigation constant N: ").strip())
                print(f"N updated to {settings.N}")
            except ValueError:
                print("Invalid input.")

        #KILL RADIUS
        elif choice == "12":
            try:
                settings.kill_radius = float(input("Enter new kill radius (m): ").strip())
                print(f"Kill radius updated to {settings.kill_radius}")
            except ValueError:
                print("Invalid input.")

        #USE EKF
        elif choice == "13":
            val = input("Enable EKF? (y/n): ").strip().lower()
            settings.use_ekf = (val == "y")
            print(f"EKF set to {settings.use_ekf}")

        #USE REAL IMU
        elif choice == "14":
            val = input("Use real IMU hardware? (y/n): ").strip().lower()
            settings.use_imu = (val == "y")
            print(f"Use IMU set to {settings.use_imu}")

        #SENSOR AZ SIGMA
        elif choice == "15":
            try:
                settings.sensor_az_sigma = float(input("Enter azimuth noise sigma (deg): ").strip())
                print(f"Az sigma updated to {settings.sensor_az_sigma}")
            except ValueError:
                print("Invalid input.")

        #SENSOR EL SIGMA
        elif choice == "16":
            try:
                settings.sensor_el_sigma = float(input("Enter elevation noise sigma (deg): ").strip())
                print(f"El sigma updated to {settings.sensor_el_sigma}")
            except ValueError:
                print("Invalid input.")

        #SENSOR AZ BIAS
        elif choice == "17":
            try:
                settings.sensor_az_bias = float(input("Enter azimuth bias (deg): ").strip())
                print(f"Az bias updated to {settings.sensor_az_bias}")
            except ValueError:
                print("Invalid input.")

        #SENSOR EL BIAS
        elif choice == "18":
            try:
                settings.sensor_el_bias = float(input("Enter elevation bias (deg): ").strip())
                print(f"El bias updated to {settings.sensor_el_bias}")
            except ValueError:
                print("Invalid input.")

        #IMU PORT
        elif choice == "19":
            settings.imu_port = input("Enter IMU serial port (e.g. COM4): ").strip()
            print(f"IMU port updated to {settings.imu_port}")

        #IMU BAUD
        elif choice == "20":
            try:
                settings.imu_baud = int(input("Enter IMU baud rate: ").strip())
                print(f"IMU baud updated to {settings.imu_baud}")
            except ValueError:
                print("Invalid input.")