#IMPORT LIBRARIES
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from Config.settings import settings

#COLORS AND LABELS FOR EACH GUIDANCE LAW
mode_colors = {
    "PN"    :   "steelblue",
    "APN"   :   "darkorange",
    "ZEM"   :   "green",
}
motion_labels = {
    "constant_velocity"     :   "CV",
    "constant_acceleration" :   "CA",
    "weaving"               :   "Weave"
}

#MASTER PLOT FUNCTION
def plot_monte_carlo(mc_output, summary):
    modes = mc_output["modes"]
    n_trials = mc_output["n_trials"]
    result = mc_output["results"]

    #3X2 GRID WITH 6 SUBPLOTS
    fig = plt.figure(figsize = (16,14))
    gs = gridspec.GridSpec(3,2,figure = fig, hspace = .5, wspace = .35)

    #HIT RATE BAR CHART AND MISS DISTANCE(LEFT/RIGHT RESPECTIVELY)
    _plot_hit_rate_bar(fig.add_subplot(gs[0,0]), summary, modes, n_trials)
    _plot_miss_cdf(fig.add_subplot(gs[0, 1]), result, modes)

    #MOTION MODEL BREAKDOWN AND CONVERGENCE(LEFT/RIGHT RESPECTIVELY)
    _plot_motion_breakdown(fig.add_subplot(gs[1,0]), summary, modes)
    _plot_convergence(fig.add_subplot(gs[1,1]), summary, modes)

    #SATURATION AND TERMINATION REASONS(LEFT/RIGHT RESPECTIVELY)
    _plot_saturation(fig.add_subplot(gs[2,0]), result, modes)
    _plot_termination(fig.add_subplot(gs[2,1]), summary, modes)

    #MASTER TITLE 
    fig.suptitle(f"Monte Carlo Analysis - {n_trials} Trials per Mode", fontsize = 14, fontweight = "bold")

    plt.tight_layout()
    plt.show()
    return fig

#PLOT 1 FOR HIT RATE BAR-95% WILSON CONFIDENCE INTERVAL
def _plot_hit_rate_bar(ax, summary, modes, n_trials):

    #GRAB HIT RATES AND CONFIDENCE INTERVAL BOUNDS
    hit_rates = [summary[m]["hit_rate"] for m in modes]
    ci_lows = [summary[m]["ci_low"] for m in modes]
    ci_highs = [summary[m]["ci_high"] for m in modes]
    colors = [mode_colors[m] for m in modes]

    #ERROR BAR LENGTHS FROM HIT RATE TO EACH CI BOUND FOR DISTANCE
    err_low = [hit_rates[i]-ci_lows[i] for i in range(len(modes))]
    err_high = [ci_highs[i]-hit_rates[i] for i in range(len(modes))]

    #DRAW BARS
    bars = ax.bar(modes, hit_rates, color = colors, edgecolor = "black", linewidth = .7, alpha = .85)

    #OVERLAY CI ERROR BARS
    ax.errorbar(modes, hit_rates, yerr=[err_low, err_high], fmt = "none", color = "black", capsize = 6, linewidth = 1.5)

    #LABEL EACH BAR WITH HIT RATE
    for bar, rate in zip(bars, hit_rates):
        ax.text(bar.get_x() + bar.get_width()/2,
                bar.get_height()+4.0,
                f"{rate:.1f}%", ha = "center", va = "bottom", fontsize = 9)
    ax.set_ylabel("Hit Rate (%)")

    #YLIM TO 115 FOR ROOM ABOVE BAR
    ax.set_ylim(0,115)
    ax.set_title("Intercept Probability with 95% CI")
    
    #INTERPRETATION
    ax.text(.98,.05,"Higher is better.\nError bars show 95% Wilson Confidence Interval",
            transform = ax.transAxes, fontsize = 7, ha = "left", va = "top", bbox = dict(boxstyle="round,pad=.3", facecolor="lightyellow", alpha=.8))

    #HORIZONTAL GRID ONLY SO BARS AREN'T HARD TO READ
    ax.grid(True, alpha = .3, axis = "y")

#PLOT 2 MISS DISTANCE CUMULATIVE DISTRIBUTION FUNCTION (CDF) FOR NON-HIT TRIALS
def _plot_miss_cdf(ax, results, modes):

    for mode in modes:
        #FILTER TO NON HIT TRIALS WITH NON-NAN MISS DISTANCES
        #SORT INCREASING SO CDF GOES UP LEFT TO RIGHT
        misses = sorted([t["miss_distance"] for t in results[mode]
                         if not t["hit"] and not np.isnan(t['miss_distance'])])
        
        #SKIP MODE IF THERE'S NO MISSES
        if not misses:
            continue

        #CDF Y VALUES
        cdf = np.arange(1,len(misses)+1)/len(misses)
        ax.plot(misses, cdf, color = mode_colors[mode], lw = 2, label = mode)
        
    ax.axvline(x=settings.kill_radius, color = "black", linestyle="--", lw = 1.5, label = f"Kill Radius ({settings.kill_radius}m)")
    ax.set_xlabel("Miss Distance (m)")
    ax.set_ylabel("CDF")
    ax.set_title("Miss Distance CDF (non-hit trials)")

    #INTERPRETATION
    ax.text(.98,.05,"Curve left means smaller misses, which is better.\nOnly failed intercepts shown.",
            transform = ax.transAxes, fontsize = 7, ha = "left", va = "top", bbox = dict(boxstyle="round,pad=.3", facecolor="lightyellow", alpha=.8))

    ax.legend(fontsize = 9)
    ax.grid(True, alpha = .3)

#PLOT 3 HIT RATE BY TARGET MOTION MODEL
def _plot_motion_breakdown(ax, summary, modes):
    motion_types = ["constant_velocity", "constant_acceleration", "weaving"]

    #X POSITION AND WIDTH OF GROUPS
    x = np.arange(len(motion_types))
    width = .25

    for i, mode in enumerate(modes):
        rates = []
        for mt in motion_types:
            bd = summary[mode]['motion_breakdown'].get(mt, {"hit_rate"  :   0.0})
            rates.append(bd['hit_rate'])
        
        #OFFSET SO THEY'RE SIDE BY SIDE
        ax.bar(x+i*width, rates, width,
                label = mode, color = mode_colors[mode],
                alpha = .85, edgecolor = "black", linewidth = .5)
        
    #CENTER TICK LABELS BETWEEN BARS
    ax.set_xticks(x+width)
    ax.set_xticklabels([motion_labels[mt] for mt in motion_types])
    ax.set_ylabel("Hit Rate (%)")
    ax.set_ylim(0,115)
    ax.set_title("Hit Rate by Target Motion Model")

    #INTERPRETATION
    ax.text(.98,.05,"Shows which law handles each threat type best.",
            transform = ax.transAxes, fontsize = 7, ha = "left", va = "top", bbox = dict(boxstyle="round,pad=.3", facecolor="lightyellow", alpha=.8))

    ax.legend(fontsize = 9)
    ax.grid(True, alpha = .3, axis = "y")

#PLOT 4 - STATISTICAL CONVERGENCE
def _plot_convergence(ax, summary, modes):
    #CYCLE THROUGH MODES
    for mode in modes:
        #GRAB CONVERGENCE
        conv = summary[mode]["convergence"]
        #PASS IF IT'S NOT CONVERGING
        if not conv:
            continue

        #GRAB TRIAL COUNT AND RUNNING HIT RATES
        n_vals = [c["n"] for c in conv]
        rate_vals = [c["hit_rate"] for c in conv]

        #MARKERS FOR CHECKPOINT VISIBILITY
        ax.plot(n_vals, rate_vals, color = mode_colors[mode], lw=1.8,marker='o',markersize=4,label=mode)

    #LABELS
    ax.set_xlabel("Trial Count")
    ax.set_ylabel("Running Hit Rate (%)")
    ax.set_title("Statistical Convergence")

    #INTERPRETATION
    ax.text(.98,.05,"Flat lines means estimate is stable\nStill moving means it may needs more trials",
            transform = ax.transAxes, fontsize = 7, ha = "left", va = "top", bbox = dict(boxstyle="round,pad=.3", facecolor="lightyellow", alpha=.8))

    ax.legend(fontsize = 9)
    ax.grid(True, alpha = .3)

#PLOT 5 AUTOPILOT SATURATION FRACTION BOX PLOTS
def _plot_saturation(ax, results, modes):
    #LIST OF SATURATION % PER MODE
    sat_data = [
        [t["saturation_fraction"]*100 for t in results[mode]] for mode in modes
    ]

    #FILL BOX WITH COLOR
    bp = ax.boxplot(sat_data,labels=modes,patch_artist=True,medianprops={
        "color": "black",
        "lw"    : 1.5})
    
    #COLOR EACH BOX MATCHING WITH GUIDANCE LAW COLOR
    for patch,mode in zip(bp["boxes"], modes):
        patch.set_facecolor(mode_colors[mode])
        patch.set_alpha(.7)
    
    #LABELS
    ax.set_ylabel("Saturation Fraction (%)")
    ax.set_title("Autopilot Saturation Distribution")

    #INTERPRETATION
    ax.text(.98,.05,"Fraction of flight at max accel.\nHigh means no control margin remaining",
                transform = ax.transAxes, fontsize = 7, ha = "right", va = "top", bbox = dict(boxstyle="round,pad=.3", facecolor="lightyellow", alpha=.8))

    ax.grid(True, alpha = .3, axis = "y")

#PLOT 6 TERMINATION REASON BAR CHART
def _plot_termination(ax,summary,modes):
    #FIXED COLOR FOR EACH REASON
    reason_colors = {
        "hit"   :   "green",
        "diverged"  :   "crimson",
        "timeout_closing"   :   "steelblue",
        "timeout_receding"  :   "darkorange",
        "error"             :   "gray"
    }

    #GRAB ALL REASONS FOR TERMINATIONS
    all_reasons = sorted(set(reason
                              for mode in modes 
                              for reason in summary[mode]["termination_counts"].keys()))

    #DICT OF REASONS SO EACH ONE HAS A LIST OF % READY TO PLOT
    reason_pcts = {}
    for reason in all_reasons:
        reason_pcts[reason] = [summary[mode]["termination_counts"].get(reason,0)/summary[mode]["n"]*100
                                for mode in modes]
    
    #STACK EACH REASON ON TOP OF THE PREVIOUS ONE
    bottoms = np.zeros(len(modes))
    for reason, pcts in reason_pcts.items():
        ax.bar(modes, pcts, bottom = bottoms, label = reason, color = reason_colors.get(reason,"purple"),edgecolor="black",linewidth=.5,alpha=.85)
        bottoms += np.array(pcts)

    #TITLE
    ax.set_ylabel("Percentage of Trials (%)")
    ax.set_ylim(0,115)
    ax.set_title("Termination Reason Breakdown")

    #INTERPRETATION
    ax.text(.98,.05,"Green means hit. Red means diverged.\nBlue/orange = timeout",
                transform = ax.transAxes, fontsize = 7, ha = "left", va = "top", bbox = dict(boxstyle="round,pad=.3", facecolor="lightyellow", alpha=.8))

    ax.legend(fontsize=8, loc = "upper right")
    ax.grid(True, alpha = .3, axis = "y")