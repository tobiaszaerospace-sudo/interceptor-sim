#ACTUALLY RECORD AND SAVE THE DATA
#IMPORT STUFF
import time
import cv2
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