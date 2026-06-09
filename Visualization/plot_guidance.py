#IMPORT LIBRARIES
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

#GUIDANCE ANALYSIS PLOT
def plot_guidance_analysis(history, title_suffix = ""):
    #GRAB DATA FROM HISTORY AS THEIR OWN ARRAYS
    t = np.array([s["t"] for s in history])
    rng = np.array([s["range"] for s in history])
    Vc = np.array([s["closing_velocity"] for s in history])
    los_ang = np.array([s["los_angle"] for s in history])
    los_rate = np.array([np.linalg.norm(s["los_rate"]) for s in history])
    a_cmd = np.array([np.linalg.norm(s['a_command']) for s in history])
    a_act = np.array([s['accel_mag'] for s in history])
    r_rel = np.array([s['r_rel'] for s in history])
    v_rel = np.array([s['v_rel'] for s in history])

    #ZEM VALUE - 0th ORDER
    #T_GO NEEDS TO BE FOUND AT EACH STEP, DROP IF Vc IS TOO LOW TO AVOID ERROR
    t_go = np.where(Vc>.1, rng/Vc, np.nan)
    #ZEM VALUES FOR EACH STEP USING ZEROETH ORDER, IF Vc MADE A NP.NAN THEN DROP COMPUTION
    zem = np.array([np.linalg.norm(r_rel[i]+v_rel[i]*t_go[i]) if not np.isnan(t_go[i]) else np.nan for i in range(len(t))])

    #START UP SUFFIX SO DON'T HAVE TO REPEAT IT EVERY TITLE
    suf = f" - {title_suffix}" if title_suffix else ""

    #FIGURE LAYOUT AND GRID SPACING
    fig = plt.figure(figsize = (14,10))
    gs = gridspec.GridSpec(3,2,figure = fig,hspace=.45,wspace=.35)

    #PLOT 1 - LOS ANGLE V TIME
    ax1 = fig.add_subplot(gs[0,0])
    ax1.plot(t, los_ang, color = 'steelblue', lw=1.5)
    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("LOS Angle (deg)")
    ax1.set_title(f"LOS Angle vs Time{suf}")
    ax1.grid(True, alpha = .35)

    #PLOT 2 - LOS RATE V TIME
    ax2 = fig.add_subplot(gs[0,1])
    ax2.plot(t, np.degrees(los_rate), color = 'darkorange', lw=1.5)
    ax2.set_xlabel("Time (s)")
    ax2.set_ylabel("LOS Rate (deg/s)")
    ax2.set_title(f"LOS Rate vs Time{suf}")
    ax2.grid(True, alpha = .35)

    #PLOT 3 - RANGE AND CLOSING VELOCITY V TIME
    ax3 = fig.add_subplot(gs[1,0])
    ax3_r = ax3.twinx()
    l1, = ax3.plot(t,rng,color="navy",lw=1.5,label="Range (m)")
    l2, = ax3_r.plot(t,Vc,color="crimson", lw = 1.5,linestyle="--", label = "Vc (m/s)")
    ax3.set_xlabel("Time (s)")
    ax3.set_ylabel("Range (m)", color = "navy")
    ax3_r.set_ylabel("Closing Velocity (m/s)", color = "crimson")
    ax3.set_title(f"Range and Closing Velocity vs Time{suf}")
    ax3.legend(handles = [l1,l2], loc = "upper right", fontsize = 8)
    ax3.grid(True,alpha=.35)

    #PLOT 4 - COMMANDED VS ACHIEVED ACCELERATION VS TIME
    ax4 = fig.add_subplot(gs[1,1])
    ax4.plot(t,a_cmd/9.81,color="green",lw=1.5,label="Commanded Acceleration")
    ax4.plot(t,a_act/9.81,color="purple", lw = 1.5, linestyle = "--", label = "Achieved Acceleration")
    ax4.set_xlabel("Time (s)")
    ax4.set_ylabel("Acceleration (G's)")
    ax4.set_title(f"Commanded vs Achieved Acceleration vs Time{suf}")
    ax4.legend(fontsize = 8)
    ax4.grid(True, alpha = .35)

    #PLOT 5 - ZEM V TIME
    ax5 = fig.add_subplot(gs[2,0])
    ax5.plot(t,zem,color="teal",lw=1.5)
    ax5.axhline(0,color="black", linestyle = ":", lw = .8)
    ax5.set_xlabel("Time (s)")
    ax5.set_ylabel("Zero Effort Miss (m)")
    ax5.set_title(f"Zero Effort Miss vs Time{suf}")
    ax5.grid(True, alpha = .35)

    #PLOT 6 - LOS RATE * RANGE (LATERAL DEVIATION RATE)
    ax6 = fig.add_subplot(gs[2,1])
    ax6.plot(t,np.degrees(los_rate)*rng, color = "saddlebrown", lw = 1.5)
    ax6.set_xlabel("Time (s)")
    ax6.set_ylabel("LOS Rate * Range (m*deg/s)")
    ax6.set_title(f"Lateral Deviation Rate vs Time {suf}")
    ax6.grid(True, alpha = .35)

    #CLEAN UP/SHOW PLOTS
    fig.suptitle(f"Guidance Analysis Plots{suf}", fontsize = 15, fontweight = "bold")
    plt.tight_layout()
    plt.show()

    return fig