#ACTUALLY RECORD AND SAVE THE DATA
#IMPORT STUFF
import time
import cv2
import os
import json
from Sensors.tracking import Tracker
from Sensors.stereo_depth import split_frame, focal_length_px, estimate_depth
from Detection_Data_Processing.los_computation import LOSComputer
from Config.settings import settings

#FUNCTION FOR STARTING AND STOPPING DATA COLLECTION
def record_target_motion():
    print("\nStarting live target motion recording. Press ESC to stop and use data")

    #SETUP VARIABLES AND OBJECTS
    tracker = Tracker()
    los = LOSComputer(
        camera_fov_degrees = settings.camera_fov_x,
        image_width = settings.image_width,
        image_height = settings.image_height,
    )
    focal_px = focal_length_px(settings.image_width, settings.camera_fov_x)
    records = []
    start_time = time.time()

    #MAIN ATTEMPT
    try:
        while True:
            #CAPTURE AND SPLIT FRAME
            frame = tracker.camera.read()
            left, right = split_frame(frame)

            #DETECT IN BOTH
            det_left = tracker.detect_yolo(left)
            det_right = tracker.detect_yolo(right)

            #CHECK IF BOTH ARE VALID
            if det_left["valid"] and det_right['valid']:
                #BASE CALCULATIONS OFF LEFT, GRAB DISPARITY OFF DIFFERENCE IN L AND R
                cx, cy = det_left["cx"], det_left["cy"]
                disparity_px = det_left['cx'] - det_right['cx']

                #GET DISTANCE
                distance = estimate_depth(disparity_px, settings.stereo_baseline, focal_px)

                #IF DISTANCE IS VALID, COMPUTE VALUES, RECORD, AND ANNOUNCE
                if distance is not None:
                    angles = los.compute_los_angles(cx, cy)
                    t = time.time() - start_time
                    records.append({
                        "timestamp" : t,
                        "angle_x" : angles["angle_x"],
                        "angle_y" : angles["angle_y"],
                        "range_m" : distance,
                    })
                    print(f"[REC] t={t:6.2f}s  az={angles['angle_x']:7.2f} deg  "
                          f"el={angles['angle_y']:7.2f} deg  range={distance:6.2f} m")

                    #ADD A CIRCLE TO SEE IF IT'S ON THE RED YOLO DOT
                    cv2.circle(left, (int(cx), int(cy)), 6, (0,0,225), -1)

                #IF DISTANCE ISN'T VALID, SAY SO
                else:
                    print("[REC] Target seen in both lenses but disparity was invalid")

            #IF WASN'T DETECTED IN BOTH LENSES
            else:
                print("[REC] Target not detected in both lenses")

            #SHOW IMAGE
            cv2.imshow("Recording target motion (ESC to stop)", left)
            if cv2.waitKey(1) == 27:
                break

    #REELEASE AND CLOSE WINDOWS
    finally:
        tracker.camera.release()
        cv2.destroyAllWindows()

    #CHECK FOR SMALL RUNTIMES
    if len(records) < 4:
        raise RuntimeError("Not enough data points recorded. Try again with a clearer and longer view of the target")

    #RETURN DATA
    return records

#SAVE A RECORDING TO DISK SO IT CAN BE REUSED FOR MONTE CARLO
def save_recording(records, folder = "Recordings"):
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"clip_{int(time.time()*1000)}.json")
    with open(path, "w") as f:
        json.dump(records, f)
    return path

#LOAD EVERY SAVED CLIP IN FOLDER INTO LIST OF RECORD LISTS (MONTE CARLO POOL)
def load_recording_pool(folder="Recordings"):
    if not os.path.isdir(folder):
        return []
    pool = []
    for fname in sorted(os.listdir(folder)):
        if fname.endswith(".json"):
            with open(os.path.join(folder, fname)) as f:
                pool.append(json.load(f))
        return pool

#RECORD SEVERAL CLIPS IN A ROW AND SAVE UNTIL STOPPED
def record_batch():
    print("Recording a library of target motion clips for Monte Carlo")
    print("You'll record one clip at a time) Press ESC during each to stop")
    count = 0
    while True:
        records = record_target_motion()
        path = save_recording(records)
        count += 1
        print(f"Saved clip #{count} to {path}")
        again = input("Record another clip? (y/n): ").strip().lower()
        if again != 'y':
            break
    print(f"Done. {count} clip(s) saved to the Recordings folder.")

#LIST ALL SAVED CLIP FILENAMES
def list_recordings(folder="Recordings"):
    if not os.path.isdir(folder):
        return []
    return sorted(f for f in os.listdir(folder) if f.endswith(".json"))

#DELETE A SAVED CLIP BY FILENAME
def delete_recording(filename, folder="Recordings"):
    path = os.path.join(folder, filename)
    if os.path.exists(path):
        os.remove(path)
        return True
    return False

#MAKE MENU FOR REVIEWING AND DELETING SAVED CLIPS
def manage_recordings(folder = "Recordings"):
    while True:
        #GET LIST OF FILES
        files = list_recordings(folder)
        #CHECK FOR NO FILES
        if not files:
            print("No recorded clips found")
            return

        #IF THERE ARE FILES
        print("\nRecorded clips:")
        for i, f in enumerate(files):
            print(f"    {i} : {f}")
            choice = input("Enter a number to delete, 'all' to delete all, or pess enter to go back: ").strip().lower()
            if choice == "":
                return
            if choice == "all":
                confirm = input(f"Delete all clips? (y/n): ").strip().lower()
                if confirm == 'y':
                    for f in files:
                        delete_recording(f, folder)
                    print("All clips deleted")
                continue
            try:
                idx = int(choice)
                if 0 <= idx < len(files):
                    deleted_name = files[idx]
                    delete_recording(deleted_name, folder)
                    print(f"Deleted {deleted_name}")
                else:
                    print("Invalid index.")
            except ValueError:
                print("Invalid input.")
        