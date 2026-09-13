#COMPARE PREDICTION FROM PREVIOUS TIMESTEP TO ACTUAL LOCATION

#IMPORT LIBRARIES
import numpy as np
import matplotlib.pyplot as plt

#COMPUT POSITION ERROR OVER TIME
def compute_prediction_errors(history, lookahead):
    #GET DATA
    t = np.array([s["t"] for s in history])
    pos = np.array([s['target_pos'] for s in history])
    vel = np.array([s['target_vel'] for s in history])
    acc = np.array([s['target_accel'] for s in history])

    #GET TIME AND LENGTH DATA RIGHT
    dt = t[1] - t[0] if len(t) < 1 else .01
    step_ahead = max(1,round(lookahead/dt))
    n = len(t) - step_ahead

    #CHECK IF SIM IS SHORT
    if n <= 0:
        raise ValueError("Recording/sim is too short for the chosen lookahead")

    #SETUP ERROR VALUES
    t_eval = t[:n]
    err0 = np.zeros(n)
    err1 = np.zeros(n)
    err2 = np.zeros(n)

    #COMPARE ACTUAL FUTURE AND PREDICTED
    for i in range(n):
        #GET ACTUAL FUTURE
        actual_future = pos[i+step_ahead]
        dt_actual = t[i+step_ahead]-t[i]

        #0TH ORDER CALCULATION
        pred0 = pos[i]

        #1ST ORDER CALCULATION
        pred1 = pos[i] + vel[i]*dt_actual

        #2ND ORDER CALCULATION
        pred2 = pos[i] + vel[i]*dt_actual + .5*acc[i]*dt_actual**2

        #CALCULATE ERRORS
        err0[i] = np.linalg.norm(actual_future-pred0)
        err1[i] = np.linalg.norm(actual_future-pred1)
        err2[i] = np.linalg.norm(actual_future-pred2)

    #RETURN VALUES
    return t_eval, err0, err1, err2

#PLOT PREDICTION ERROR OVER TIME 
def plot_prediction_analysis(history, lookahead=0.2, title_suffix=""):
    t_eval, err0, err1, err2 = compute_prediction_errors(history, lookahead)

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(t_eval, err0, label="0th order (assumes no motion)", color="firebrick")
    ax.plot(t_eval, err1, label="1st order (constant velocity)", color="darkorange")
    ax.plot(t_eval, err2, label="2nd order (constant acceleration)", color="seagreen")

    ax.set_xlabel("Time (s)")
    ax.set_ylabel(f"Position error at t+{lookahead:.2f}s (m)")
    title = f"Target Motion Prediction Error ({lookahead:.2f}s lookahead)"
    if title_suffix:
        title += f" -- {title_suffix}"
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)

    print(f"Mean prediction error -- 0th: {np.mean(err0):.2f} m, "
          f"1st: {np.mean(err1):.2f} m, 2nd: {np.mean(err2):.2f} m")

    plt.tight_layout()
    plt.show()

