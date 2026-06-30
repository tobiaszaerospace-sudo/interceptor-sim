#IMPORT LIBRARIES
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

#CONSTANT COLOR CONVENTION FROM MONTE CARLO PLOTTING
mode_colors = {
    "PN"    :   "steelblue",
    "APN"   :   "darkorange",
    "ZEM"   :   "green",
}

#MASTER PLOT FUNCTION
def plot_sweep(sweep_output):
    #STORE VARIABLES
    var_name = sweep_output["var_name"]
    spec = sweep_output["spec"]
    modes = sweep_output["modes"]
    levels = sweep_output["levels"]
    trials_per_step = sweep_output["trials_per_step"]
    sweep_results = sweep_output["sweep_results"]

    #2X2 GRID WITH 4 SUBPLOTS
    fig = plt.figure(figsize = (16,11))
    gs = gridspec.GridSpec(2,2,figure=fig,hspace=.4,wspace=.3)

    #DIFFERENT PLOTS
    _plot_hit_rate_vs_level(fig.add_subplot(gs[0,0]), sweep_results, modes, spec)
    _plot_miss_vs_level(fig.add_subplot(gs[0, 1]), sweep_results, modes, spec)
    _plot_saturation_vs_level(fig.add_subplot(gs[1, 0]), sweep_results, modes, spec)
    _plot_tti_vs_level(fig.add_subplot(gs[1, 1]), sweep_results, modes, spec)

    fig.suptitle(f"Sensitivy Sweep - {spec['label']}  ({trials_per_step} trials/step)", fontsize = 14, fontweight = "bold")
    plt.tight_layout()
    plt.show()
    return fig

#PLOT 1 HIT RATE VS SWEEP LEVEL
def _plot_hit_rate_vs_level(ax, sweep_results, modes, spec):
    #CYCLE THROUGH MODES
    for mode in modes:
        #DEFINE VARIABLES
        data = sweep_results[mode]
        levels = [d["level"] for d in data]
        rates = [d["hit_rate"] for d in data]
        ci_low = [d["ci_low"] for d in data]
        ci_high = [d["ci_high"] for d in data]

        ax.plot(levels, rates, color = mode_colors[mode], lw = 2, marker = "o", markersize = 5, label = mode)
        #SHADED CI BAND, CLEARER WHEN COMPARING 3 OVERLAPPING LINES
        ax.fill_between(levels, ci_low, ci_high, color = mode_colors[mode], alpha = .15)

    #LABELS 
    ax.set_xlabel(f"{spec['label']}  ({spec['units']})" if spec['units'] else spec['label'])
    ax.set_ylabel("Hit Rate  (%)")
    ax.set_ylim(0,115)
    ax.set_title("Intercept Probability vs. Sweep Level (shaded = 95% Wilson CI)")

    #DESCRIPTION
    ax.text(.98, .05, "Where lines diverge, guidance law choice matters.\nWhere they overlap, laws perform the same.",
        transform=ax.transAxes, fontsize=7, ha="right", va="bottom",
        bbox=dict(boxstyle="round,pad=.3", facecolor="lightyellow", alpha=.8))
    
    #CLEANING BOX UP
    ax.legend(fontsize = 9)
    ax.grid(True, alpha = .3)

#PLOT 2 MEDIAN MISS DISTANCE VS LEVEL
def _plot_miss_vs_level(ax, sweep_results, modes, spec):
    #LOOP THROUGH MODES
    for mode in modes:
        #CREATE VARIABLES
        data = sweep_results[mode]
        levels = [d["level"] for d in data]
        miss_med = [d["miss_median"] for d in data]
        ax.plot(levels, miss_med, color = mode_colors[mode], lw = 2, marker = "o", markersize = 5, label = mode)

    #SET TITLES
    ax.set_xlabel(f"{spec['label']} ({spec['units']})" if spec['units'] else spec['label'])
    ax.set_ylabel("Median Miss Distance, non-hits (m)")
    ax.set_title("Miss Distance vs. Sweep Level")

    #DESCRIPTION
    ax.text(.98, .05, "NaN gaps mean every trial at that level was a hit\n(no misses to compute a median from).",
            transform=ax.transAxes, fontsize=7, ha="right", va="bottom",
            bbox=dict(boxstyle="round,pad=.3", facecolor="lightyellow", alpha=.8))
    
    #MAKE PLOT CLEAN
    ax.legend(fontsize = 9)
    ax.grid(True, alpha = .3)

#PLOT 3 AUTOPILOT SATURATION VS LEVEL
def _plot_saturation_vs_level(ax, sweep_results, modes, spec):
    #CYCLE THROUGH MODES
    for mode in modes:
        #LABEL VARIABLES
        data = sweep_results[mode]
        levels = [d["level"] for d in data]
        sat = [d["saturation_mean"] *100 for d in data]
        
        #PLOT
        ax.plot(levels, sat, color = mode_colors[mode], lw = 2, marker = 'o', markersize = 5, label = mode)

    #LABELS
    ax.set_xlabel(f"{spec['label']} ({spec['units']})" if spec['units'] else spec['label'])
    ax.set_ylabel("Mean Saturation Fraction (%)")
    ax.set_title("Autopilot Saturation vs. Sweep Level")

    #DESCRIPTION
    ax.text(.98, .05, "Rising saturation means less control margin.\nCompresses law separation - check before trusting\nthe hit-rate gap at this end of the sweep.",
            transform=ax.transAxes, fontsize=7, ha="right", va="bottom",
            bbox=dict(boxstyle="round,pad=.3", facecolor="lightyellow", alpha=.8))

    #CLEAN PLOT UP
    ax.legend(fontsize = 9)
    ax.grid(True, alpha = .3)

#PLOT 4 TIME TO INTERCEPT VS LEVEL FOR HITS ONLY
def _plot_tti_vs_level(ax, sweep_results, modes, spec):
    #CYCLE THROUGH MODES
    for mode in modes:
        #LABEL VARIABLES
        data = sweep_results[mode]
        levels = [d["level"] for d in data]
        tti = [d["tti_mean"] for d in data]
        
        #PLOT
        ax.plot(levels, tti, color = mode_colors[mode], lw = 2, marker = 'o', markersize = 5, label = mode)

    #LABELS
    ax.set_xlabel(f"{spec['label']} ({spec['units']})" if spec['units'] else spec['label'])
    ax.set_ylabel("Mean Time-to-Intercept, hits only (s)")
    ax.set_title("Engagement Duration vs. Sweep Level")

    #DESCRIPTION
    ax.text(.98, .05, "NaN gaps mean no hits occurred at that level.",
            transform=ax.transAxes, fontsize=7, ha="right", va="bottom",
            bbox=dict(boxstyle="round,pad=.3", facecolor="lightyellow", alpha=.8))

    #CLEAN PLOT UP
    ax.legend(fontsize = 9)
    ax.grid(True, alpha = .3)