from Config.settings import settings


def run_settings_menu():
    while True:
        #SHOW CURRENT SETTINGS TO USER
        print("\n --- SETTINGS MENU --- ")
        print(f"1. Camera FOV X: {settings.camera_fov_x}")
        print(f"2. Image Width: {settings.image_width}")
        print(f"3. Image Height: {settings.image_height}")
        print(f"4. Camera Index: {settings.camera_index}")
        print(f"5. FPS: {settings.fps}")
        print(f"6. Servo Port: {settings.servo_port}")
        print(f"7. Servo Baud: {settings.servo_baud}")
        print(f"8. YOLO Model Path: {settings.yolo_model_path}")
        print("9. Return to Main Menu")
        choice = input("Enter the number of the setting you want to change or exit program (1-9): ").strip()
        #VALIDATE INPUT
        while choice not in [str(i) for i in range(1, 10)]:
            print("Invalid input. Please enter a number between 1 and 9.")
            choice = input("Enter the number of the setting you want to change or exit program (1-9): ").strip()
        if choice == "9":
            print("Returning to Main Menu...")
            break
        #CAMERA FOV
        elif choice == "1":
            try:
                new_fov = float(input("Enter new Camera FOV X in degrees: ").strip())
                settings.camera_fov_x = new_fov
                print(f"Camera FOV X updated to {new_fov} degrees.")
            except ValueError:
                print("Invalid input. Please enter a valid number.")
        #IMAGE WIDTH
        elif choice == "2":
            try:
                new_width = int(input("Enter new Image Width in pixels: ").strip())
                settings.image_width = new_width
                print(f"Image Width updated to {new_width} pixels.")
            except ValueError:
                print("Invalid input. Please enter a valid integer.")
        #IMAGE HEIGHT
        elif choice == "3":
            try:
                new_height = int(input("Enter new Image Height in pixels: ").strip())
                settings.image_height = new_height
                print(f"Image Height updated to {new_height} pixels.")
            except ValueError:
                print("Invalid input. Please enter a valid integer.")
        #CAMERA INDEX
        elif choice == "4":
            try:
                new_index = int(input("Enter new Camera Index (integer): ").strip())
                settings.camera_index = new_index
                print(f"Camera Index updated to {new_index}.")
            except ValueError:
                print("Invalid input. Please enter a valid integer.")
        #FPS
        elif choice == "5":
            try:
                new_fps = int(input("Enter new FPS (integer): ").strip())
                settings.fps = new_fps
                print(f"FPS updated to {new_fps}.")
            except ValueError:
                print("Invalid input. Please enter a valid integer.")
        #SERVO PORT
        elif choice == "6":
            new_port = input("Enter new Servo Port (e.g., COM3 or /dev/ttyUSB0): ").strip()
            settings.servo_port = new_port
            print(f"Servo Port updated to {new_port}.")
        #SERVO BAUD
        elif choice == "7":
            try:
                new_baud = int(input("Enter new Servo Baud Rate (integer): ").strip())
                settings.servo_baud = new_baud
                print(f"Servo Baud Rate updated to {new_baud}.")
            except ValueError:
                print("Invalid input. Please enter a valid integer.")
        #YOLO MODEL PATH
        elif choice == "8":
            new_path = input("Enter new YOLO Model Path: ").strip()
            settings.yolo_model_path = new_path
            print(f"YOLO Model Path updated to {new_path}.")