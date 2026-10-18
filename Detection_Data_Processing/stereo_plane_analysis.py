#AIRCRAFT TRACKING MODULE, DIFFERENT THAN HUMAN TRACKER BECAUSE OF THE WAY THE CAMERA IS SET UP

#IMPORT STUFF
from __future__ import annotations
import re
import cv2
import numpy as np
import torch
import matplotlib.pyplot as plt

#REPLACE ALL THE NaN ENTRIES WITH PREDICTIONS
camera_1_intrinsics = np.array([
    [1250.0, 0.0, 1920.0],
    [0.0, 1250.0, 1080.0],
    [0.0, 0.0, 1.0]
])
camera_2_intrinsics = np.array([
    [1250.0, 0.0, 1920.0],
    [0.0, 1250.0, 1080.0],
    [0.0, 0.0, 1.0]
])
camera_2_rotation_from_camera_1 = np.array([
    [-.19641, .36684, .90932],
    [-.33504, .84645, -.41384],
    [-.92151, -.38594, -.04335]
], dtype = np.float64)
camera_2_translation_from_camera_1 = np.array([637.45, -189.24, -507.04], dtype = np.float64)

#NORMALIZE CROP CONTAINING TIMECODE OVERLAY
timecode_roi = (.7, 0, 1.0, .18)

#YOLO MODEL FOR COCO
airplane_class_id = 4

#MAKE SURE IT RUNS ON THE GPU
def require_cuda() -> torch.device:
    if not torch.cuda.is_available():
        raise RuntimeError("Cuda isn't available.")
    return torch.device("cuda:0")

#BUILD BOTH PROJECTION MATRICES WITH CAM 1 AS REFERENCE FRAME ORIGIN
def build_camera_projections():
    #BUILD BOTH MATRICES WITH CAM 1 AS XYZ REFRENCE FRAME
    calibration = (
        ("camera_1_intrinsics", camera_1_intrinsics, (3,3)),
        ("camera_2_intrinsics", camera_2_intrinsics, (3,3)),
        ("Camera_2_rotation_from_camera_1", camera_2_rotation_from_camera_1, (3,3)),
        ("Camera_2_translation_from_camera_1", camera_2_translation_from_camera_1, (3,)),
    )
    for name, value, shape in calibration:
        if value.shape != shape or not np.all(np.isfinite(value)):
            raise ValueError(f"Fill {name} with calibrated finite values before processing video")
    extrinsic1 = np.column_stack((np.eye(3), np.zeros(3)))
    extrinsic2 = np.column_stack((camera_2_rotation_from_camera_1, camera_2_translation_from_camera_1))

    return camera_1_intrinsics @ extrinsic1, camera_2_intrinsics @ extrinsic2

#BUILD THE TIMESTAMP READER
def build_timestamp_reader():
    try:
        import easyocr
    except ImportError as exc:
        raise RuntimeError("Install EasyOCR to read the camera timecode") from exc
    return easyocr.Reader(["en"], gpu=True, verbose = False)

#ACTUALLY READ THE TIMESTAMP
def read_timestamp(reader, frame: np.ndarray) -> str | None:

    #CROP TIME DATA
    height, width = frame.shape[:2]
    x0, y0, xi, y1 = timecode_roi
    crop = frame[int(height*y0):int(height*y1), int(width*x0):int(width*xi)]

    #IF THERES NO TIMECODE THERE, RETURN NOTHING
    if crop.size == 0:
        return None

    #READ TIMESTAMP
    for text in reader.readtext(crop, detail=0, paragraph=False):
        compact = re.sub(r"\s+", "", str(text))
        match = re.search(
    r"(\d{2})[:.](\d{2})[:.](\d{2})(?:[.,:]\d{1,3})?", compact)

        if match:
            return ":".join(match.groups())
    return None

#CONVERT HH MM SS TO PURE SECONDS
def timestamp_seconds(timestamp: str) -> int | None:
    match = re.match(r"^(\d{2}):(\d{2}):(\d{2})", timestamp)
    if not match:
        return None
    hours, minutes, seconds = map(int, match.groups())
    if hours > 23 or minutes > 59 or seconds > 59:
        return None
    return hours*3600 + minutes*60 + seconds

#COUNT FRAMES AND USE TIMESTAMPS
def timed_frames(cap, reader, fps: float):

    #SET UP VARIABLES
    frame_index = 0
    previous_second = None
    seconds_ready = False
    frames_after_tick = 0
    day_offset = 0

    #START THE LOOP
    while True:
        ok, frame = cap.read()
        if not ok:
            return 
        label = read_timestamp(reader, frame)
        observed_second = timestamp_seconds(label) if label else None

        #CHECK ON START OF SIM
        if observed_second is not None:
            if previous_second is None:
                previous_second = observed_second
            elif observed_second != previous_second:
                step = (observed_second-previous_second) % 86400
                if step == 1:
                    if observed_second < previous_second:
                        day_offset += 86400
                    seconds_ready = True
                else:
                    seconds_ready = False
                previous_second = observed_second
                frames_after_tick = 0
            elif seconds_ready:
                frames_after_tick += 1
        elif seconds_ready:
            frames_after_tick += 1

        if seconds_ready and previous_second is not None:
            yield {
                "frame" : frame,
                "frame_index" : frame_index,
                "timestamp" : label,
                "time_s" : day_offset + previous_second + frames_after_tick / fps,
            }

        frame_index += 1

#DETECT THE ACTUAL AIRCRAFT
def detect_aircraft(model, frame: np.ndarray, device: torch.device, confidence:float):
    result = model.predict(frame, classes = [airplane_class_id], conf = confidence, device = str(device), imgsz = 1280, verbose = False)[0]
    if result.boxes is None or len(result.boxes) == 0:
        return None
    best = max(result.boxes, key = lambda box: float(box.conf[0].item()))
    x1,y1,x2,y2 = best.xyxy[0].detach().cpu().numpy().astype(float)
    return ((x1+x2) *.5, (y1+y2) *.5, float(best.conf[0].item()))

#GET DEPTH DIMENSION BY TRIANGULATION
def triangulate_cuda(P1: np.ndarray, P2: np.ndarray, p1, p2, device: torch.device) -> np.ndarray | None:
    #LINEAR DLT TRIANGULATION
    a = torch.as_tensor(P1, dtype=torch.float64, device = device)
    b = torch.as_tensor(P2, dtype=torch.float64, device = device)
    u1, v1 = p1
    u2, v2 = p2
    A = torch.stack((u1 * a[2] - a[0], v1 * a[2] - a[1],
                     u2 * b[2] - b[0], v2 * b[2] - b[1]))
    _, _, vh = torch.linalg.svd(A, full_matrices=False)
    Xh = vh[-1]
    if torch.abs(Xh[3]).item() < 1e-12:
        return None
    xyz = Xh[:3] / Xh[3]
    if not torch.isfinite(xyz).all().item():
        return None
    return xyz.detach().cpu().numpy()

#USE ONE CAMERAS PIXEL BEARING TO CORRECT A PREDICTED POSITION
def monocular_bearing_update(position_cam1, pixel, intrinsics, gain=.5, rotation_cam2_from_cam1 = None, translation_cam2_from_cam1 = camera_2_translation_from_camera_1):
    position_cam1 = np.asarray(position_cam1, dtype=np.float64)

    if rotation_cam2_from_cam1 is None:
        position_cam = position_cam1.copy()
    else:
        position_cam = (
            rotation_cam2_from_cam1 @ position_cam1
            + translation_cam2_from_cam1
        )

    depth = position_cam[2]
    if not np.isfinite(depth) or depth <= 1e-6:
        return position_cam1

    u, v = pixel
    fx, fy = intrinsics[0, 0], intrinsics[1, 1]
    cx, cy = intrinsics[0, 2], intrinsics[1, 2]

    bearing_position = np.array([
        (u - cx) * depth / fx,
        (v - cy) * depth / fy,
        depth,
    ])

    correction = gain * (bearing_position - position_cam)
    correction[2] = 0.0  # Keep predicted range.

    if rotation_cam2_from_cam1 is None:
        return position_cam1 + correction

    return position_cam1 + rotation_cam2_from_cam1.T @ correction

#GENERAL VIDEO PROCESSING FUNCTION
def process_videos(video1, video2, model, timestamp_reader, device, p1, p2, confidence, fps1_override = None, fps2_override = None, sync_tolerance_frames = 1.0, show = False):
    #RETURN TIMESTAMPED CAMERA 1 FRAME XYZ OBSERVATIONS FROM MATCHED FRAMES
    
    #DEFINE VIDEOS
    cap1, cap2 = cv2.VideoCapture(video1), cv2.VideoCapture(video2)
    if not cap1.isOpened() or not cap2.isOpened():
        raise RuntimeError("Could not open both videos")

    #GET FPS VALUES
    fps1 = fps1_override or cap1.get(cv2.CAP_PROP_FPS)
    fps2 = fps2_override or cap2.get(cv2.CAP_PROP_FPS)
    if fps1 <= 0 or fps2 <= 0:
        cap1.release()
        cap2.release()
        raise RuntimeError("Couldn't determine both frame rates, pass fps data in next run")

    sync_tolerance_s = sync_tolerance_frames*max(1.0/fps1, 1.0/fps2)

    #SETUP DATA STORAGE
    records = []
    stream1 = iter(timed_frames(cap1, timestamp_reader, fps1))
    stream2 = iter(timed_frames(cap2, timestamp_reader, fps2))
    sample1, sample2 = next(stream1, None), next(stream2, None)
    first_matched_time = None
    track_position = None
    track_velocity = np.zeros(3, dtype=np.float64)
    last_track_time = None
    last_stereo_position = None
    last_stereo_time = None
    monocular_gain = .5

    #GET TIME STEPS
    try:
        while sample1 is not None and sample2 is not None:
            delta_s = sample1['time_s'] - sample2['time_s']
            if abs(delta_s) > sync_tolerance_s:
                if delta_s > 0:
                    sample1 = next(stream1, None)
                else:
                    sample2 = next(stream2, None)
                continue

            #ENSURE TIMING IS GOOD
            pair_time = .5*(sample1['time_s'] + sample2['time_s'])
            if first_matched_time is None:
                first_matched_time = pair_time
            elapsed_s = pair_time - first_matched_time

            #GET LOCATION DATA
            frame1, frame2 = sample1['frame'], sample2['frame']
            point1 = detect_aircraft(model, frame1, device, confidence)
            point2 = detect_aircraft(model, frame2, device, confidence)

            dt = 0.0 if last_track_time is None else max(0.0, pair_time - last_track_time)
            predicted = None
            if track_position is not None:
                predicted = track_position + track_velocity*dt

            xyz = None
            source = "uninitialized"

            #POINT FROM 2 DETECTION POINTS
            if point1 is not None and point2 is not None:
                measured = triangulate_cuda(p1, p2, point1[:2], point2[:2], device)

                if measured is not None and np.all(np.isfinite(measured)):
                    measured = np.asarray(measured, dtype=np.float64)

                    if last_stereo_position is not None and pair_time > last_stereo_time:
                        stereo_dt = pair_time - last_stereo_time
                        measured_velocity = (
                            measured - last_stereo_position
                        ) / stereo_dt
                        track_velocity = 0.5 * track_velocity + 0.5 * measured_velocity
                    else:
                        track_velocity = np.zeros(3, dtype=np.float64)

                    track_position = measured
                    last_stereo_position = measured.copy()
                    last_stereo_time = pair_time
                    xyz = measured
                    source = "stereo"

            #IF STEREO DIDN'T GET A POINT, USE PREVIOUS TRACK RECURSIVELY
            if xyz is None:
                if predicted is None:
                    xyz = np.full(3, np.nan, dtype=np.float64)
                    source = "single_camera_no_3d_initialization"
                else:
                    track_position = predicted

                    if point1 is not None and point2 is None:
                        track_position = monocular_bearing_update(
                            predicted, point1[:2], camera_1_intrinsics,
                            gain=monocular_gain
                        )
                        source = "camera1_bearing_update"

                    elif point2 is not None and point1 is None:
                        track_position = monocular_bearing_update(
                            predicted, point2[:2], camera_2_intrinsics,
                            gain=monocular_gain,
                            rotation_cam2_from_cam1=camera_2_rotation_from_camera_1,
                            translation_cam2_from_cam1=camera_2_translation_from_camera_1
                        )
                        source = "camera2_bearing_update"

                    else:
                        source = "constant_velocity_prediction"

                    xyz = track_position.copy()

            last_track_time = pair_time

            records.append({
                "timestamp_s": float(elapsed_s),
                "x": float(xyz[0]),
                "y": float(xyz[1]),
                "z": float(xyz[2]),
                "sync_delta_s": float(delta_s),
                "detected_cam1": point1 is not None,
                "detected_cam2": point2 is not None,
                "position_source": source,
            })

            if show and np.all(np.isfinite(xyz)):
                if point1 is not None:
                    cv2.circle(
                        frame1, (int(point1[0]), int(point1[1])),
                        6, (0, 0, 225), -1
                    )
                cv2.putText(
                    frame1,
                    f"t={elapsed_s:.3f}s XYZ={xyz[0]:.2f},{xyz[1]:.2f},{xyz[2]:.2f} ({source})",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1
                )
                cv2.imshow("Stereo aircraft research analysis", frame1)
                if cv2.waitKey(1) == 27:
                    break

            #USE TRIANGULATION TO GET 3RD POINT
            if point1 and point2:
                xyz = triangulate_cuda(p1, p2, point1[:2], point2[:2], device)

                #SYNC DATA
                
            sample1, sample2 = next(stream1, None), next(stream2, None)
    finally:
        cap1.release()
        cap2.release()
        if show:
            cv2.destroyAllWindows()
    return records

#PRINT OUT TIMESTAMP AND CAMERA 1 FRAME XYZ COORDINATES
def print_xyz(records):
    print(f"{'timestamp_s':>12} {'x':>12} {'y':>12} {'z':>12}")

    for row in records:
        print(f"{row['timestamp_s']:12.3f} {row['x']:12.3f} {row['y']:12.3f} {row['z']:12.3f}")

#PLOT TRAJECTORY
def plot_trajectory(records):
    #CHECK FOR NO DATA
    if not records:
        print("No paired records found. Check timecode, FPS, detections, etc.")
        return
    
    #PLOT STUFF
    ax = plt.figure().add_subplot(111, projection="3d")
    ax.plot([r["x"] for r in records], [r["y"] for r in records],
            [r["z"] for r in records], marker="o", markersize=3)
    ax.set(title="Stereo aircraft trajectory", xlabel="Camera 1 X",
           ylabel="Camera 1 Y", zlabel="Camera 1 Z")
    plt.tight_layout()
    plt.show()

#MAIN EXECUTION FUNCTION
def vid_analysis(settings):
    if not settings.stereo_video_1_path or not settings.stereo_video_2_path:
            print("Set both video paths in settings first")
            return

    device = require_cuda()
    p1, p2 = build_camera_projections()
    
    
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise RuntimeError("Install ultralytics to run this analysis") from exc
    model = YOLO("yolov8n.pt")
    model.to(device)

    records = process_videos(settings.stereo_video_1_path, settings.stereo_video_2_path, model, build_timestamp_reader(), device, p1, p2, settings.stereo_detection_confidence, settings.stereo_video_1_fps, settings.stereo_video_2_fps, settings.stereo_sync_tolerance_frames, settings.stereo_show_detections)
    print_xyz(records)
    plot_trajectory(records)
    return records

