#VISUALIZE PN ANALYTICAL VALIDATION RESULTS WITH PLOT
#GRAB FUNCTIONS AND FILES
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

#PLOT FUNCTION
def plot_validation(results, ic):
    #GET LENGTH OF PANELS
    n_panels = len(results)

    #MAKE A 2X2 GRIP FOR UP TO 4 N VALUES
    fig, axes = plt.subplots(2,2,figsize=(13,10))
    axes_flat = axes.flatten()

    #GRAB ENGAGEMENT PARAMS FROM IC FOR TITLE, MAKES IT AUTOMATIC 
    R0 = np.linalg.norm(ic['target_data']['initial_position'])
    Vi = np.linalg.norm(ic['vi0'])
    Vt = np.linalg.norm(ic['target_data']['initial_velocity'])
    epsilon_deg = np.degrees(np.arcsin(ic['vi0'][1]/Vi))

    #DESCRIPTION
    fig.suptitle(
        f"PN Guidance Analytical Validation — ZEM Decay vs Theory\n"
        f"R₀={R0:.0f}m  Vᵢ={Vi:.0f}m/s  Vₜ={Vt:.0f}m/s  ε={epsilon_deg:.1f}°  "
        f"Target: constant velocity\n"
        f"Theory: ZEM(t_go) = ZEM₀·(t_go/t_go₀)^N  [Zarchan adjoint method]",
        fontsize=11, fontweight="bold")
    
    #RUN THROUGH VALUES
    for idx, results in enumerate(results):
        ax = axes.flat[idx]
        N = results['N']
        t_gos = results['t_gos']
        zems = results['zems']
        measured = results['measured_slope']
        r_sq = results['r_squared']
        hit = results['hit']

        #MAKE SURE IT'S NOT AN ERROR
        if len(t_gos) < 5 or np.isnan(measured):
            ax.text(0.5, 0.5, "Insufficient data", transform=ax.transAxes,
                    ha="center", va="center", fontsize=10)
            ax.set_title(f"N = {N:.1f}")
            continue

        #SORT BY T_GO FOR CLEAN LINE
        sort_idx = np.argsort(t_gos)
        t_gos_s = t_gos[sort_idx]
        zems_s = zems[sort_idx]

        #THEORETICAL LINE, ANCHORED AT FIRST DATA POINT
        t_go0  = t_gos_s[0]
        zem0   = zems_s[0]
        t_theory = np.linspace(t_gos_s[0], t_gos_s[-1], 300)
        zem_theory = zem0 * (t_theory / t_go0) ** N

        #PLOT SIMULATED DATA AND THEORETICAL DATA
        ax.loglog(t_gos_s, zems_s, "o", color="steelblue", markersize=3,
                  alpha=0.7, label="Sim ZEM")
        ax.loglog(t_theory, zem_theory, "--", color="darkorange", lw=2,
                  label=f"Theory: slope={N:.1f}")
        
        #VERTICAL LINE AT T_GO = .3S MARKING WEHRE REGRESSION FIT STARTS
        ax.axvline(x=0.3, color="gray", lw=0.8, linestyle=":", alpha=0.7)
        ax.text(0.31, ax.get_ylim()[0] if ax.get_ylim()[0] > 0 else 1e-3,
                "fit start\n(t_go=0.3s)", fontsize=6, color="gray", va="bottom")

        #SLOPE COMPARISON ANNOTATION
        deviation_pct = abs(measured - N) / N * 100
        color = "green" if deviation_pct < 5 else ("orange" if deviation_pct < 15 else "red")
        ax.text(0.97, 0.97,
                f"Measured slope: {measured:.3f}\n"
                f"Theory slope:   {N:.3f}\n"
                f"Deviation: {deviation_pct:.1f}%\n"
                f"R^2 = {r_sq:.4f}\n"
                f"Hit: {hit}",
                transform=ax.transAxes, fontsize=8,
                ha="right", va="top",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", alpha=0.85),
                color=color)

        #CLEAN UP AXES
        ax.set_xlabel("Time-to-Go (s)")
        ax.set_ylabel("ZEM magnitude (m)")
        ax.set_title(f"N = {N:.1f}")
        ax.legend(fontsize = 8, loc = "upper left")
        ax.grid(True, which = "both", alpha = .3)

    #HIDE ANY UNUSED PANELS 
    for idx in range(n_panels, len(axes_flat)):
        axes_flat[idx].set_visible(False)
    
    #CLEAN UP
    plt.tight_layout()
    plt.show()
    return fig
