#CONVERT XYZ TO ANGLES 

#IMPORT STUFF
import numpy as np

def xyz_to_angles(samples):
    timestamps = np.asarray([sample['timestamp_s'] for sample in samples], dtype = float)
    xyz = np.asarray([[sample['x'], sample['y'], sample['z']] for sample in samples], dtype = float)
    if xyz.ndim != 2 or xyz.shape[1] != 3 or len(timestamps) != len(xyz):
        raise ValueError("Each sample must contain timstamp_s, x, y, and z")
    if not np.all(np.isfinite(timestamps)) or not np.all(np.isfinite(xyz)):
        raise ValueError("Samples must contain only finite numeric values")
    if np.any(np.diff(timestamps) <= 0):
        raise ValueError("Sample timestamps must be strictly increasing")

    x, y, z = xyz.T
    horizontal_range = np.hypot(x,y)
    ranges = np.hypot(horizontal_range, z)
    if np.any(ranges == 0):
        raise ValueError("A sample at the observed origin has undefined angles")
    
    angle_x = np.degrees(np.arctan2(y,x))
    angle_y = np.degrees(np.arctan2(z, horizontal_range))
    return [
        {"timestamp" : float(t),
        "angle_x" : float(ax),
        "angle_y" : float(ay),
        "range_m" : float(r)
        }
    for t, ax, ay, r in zip(timestamps, angle_x, angle_y, ranges)]