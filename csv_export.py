#CSV EXPORT
#IMPORT LIBRARIES
import csv
import os
from datetime import datetime

#DEFAULT LOCATION FOR ALL EXPORTS
Default_export_dir = "Data/exports"

#FUNCTION FOR MAKE SURE OUTPUT DIRECTORY EXISTS BEFORE WRITING
def _ensure_dir(path):
    os.makedirs(path, exist_ok=True)

#TIMESTAMP STRING FOR SORTABLE FILENAMES
def _timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

#WRITE LIST OF DICTIONAIRES TO CSV WITH A GIVEN COLUMN ORDER
def _write_csv(filepath, fieldnames, rows):
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames = fieldnames, extrasaction = 'ignore')
        writer.writeheader()
        writer.writerows(rows)

#MAIN EXPORT FUNCTION WRITES ALL FOUR CSV FILES INTO A SINGLE TIMESTAMP SUBFOLDER
def export_monte_carlo_csv(mc_output, summary, export_dir = Default_export_dir):
    #MAKE A FOLDER FOR THIS RUN
    run_folder = os.path.join(export_dir, _timestamp())
    _ensure_dir(run_folder)

    modes = mc_output['modes']
    results = mc_output['results']
    n_trials = mc_output['n_trials']
    seed = mc_output['master_seed']

    #FILE 1) PER-TRIAL RAW DATE. ONE ROW PER TRIAL PER MODE
    #ESTABLISH FIELDS
    trial_fields = ["trial", "mode", "motion_type", "hit", "miss_distance", "peak_accel", "avg_accel", "t_final", "saturation_fraction", "termination_reason"]
    trial_rows = []
    
    #CYCLE THROUGH MODES AND APPEND
    for mode in modes:
        for trial in results[mode]:
            trial_rows.append(trial)
    
    #SAVE
    trial_path = os.path.join(run_folder, "trial_data.csv")
    _write_csv(trial_path, trial_fields, trial_rows)

    #FILE 2) SUMMARY STATISTIC ONE ROW PER GUIDANCE LAW 
    #ESTABLISH FIELDS
    summary_fields = ["mode", "n_trials", "seed", "hit_rate", "ci_low", "ci_high", "miss_mean", "miss_std", "miss_median", "miss_95th", "all_miss_mean", "all_miss_std", "peak_accel_median", "avg_accel_median", "saturation_mean", "saturation_median", "tti_mean", "tti_std"]
    summary_rows = []

    #CYCLE THROUGH MODES AND APPEND
    for mode in modes:
        s = summary[mode]
        summary_rows.append({
            "mode"               : mode,
            "n_trials"           : n_trials,
            "seed"               : seed,
            "hit_rate"           : round(s["hit_rate"],        3),
            "ci_low"             : round(s["ci_low"],          3),
            "ci_high"            : round(s["ci_high"],         3),
            "miss_mean"          : round(s["miss_mean"],       3),
            "miss_std"           : round(s["miss_std"],        3),
            "miss_median"        : round(s["miss_median"],     3),
            "miss_95th"          : round(s["miss_95th"],       3),
            "all_miss_mean"      : round(s["all_miss_mean"],   3),
            "all_miss_std"       : round(s["all_miss_std"],    3),
            "peak_accel_median"  : round(s["peak_accel_median"], 3),
            "avg_accel_median"   : round(s["avg_accel_median"],  3),
            "saturation_mean"    : round(s["saturation_mean"],   3),
            "saturation_median"  : round(s["saturation_median"], 3),
            "tti_mean"           : round(s["tti_mean"],        3) if s["tti_mean"] == s["tti_mean"] else "N/A",
            "tti_std"            : round(s["tti_std"],         3) if s["tti_std"]  == s["tti_std"]  else "N/A",
        })

    #SAVE
    summary_path = os.path.join(run_folder, "summary_stats.csv")
    _write_csv(summary_path, summary_fields, summary_rows)

    #FILE 3) MOTION MODEL BREAKDOWN

    #ESTABLISH MOTIONS
    motion_fields = ["mode", "motion_type", "n", "hit_rate"]
    motion_rows = []

    #CYCLE THROUGH AND APPEND
    for mode in modes:
        bd = summary[mode]["motion_breakdown"]
        for mt, data in bd.items():
            motion_rows.append({
                "mode"       : mode,
                "motion_type": mt,
                "n"          : data["n"],
                "hit_rate"   : round(data["hit_rate"], 3),
            })

    #SAVE TO PATH
    motion_path = os.path.join(run_folder, "motion_breakdown.csv")
    _write_csv(motion_path, motion_fields, motion_rows)

    #FILE 4) CONVERGENCE DATA ONE ROW PER CHECKPOINT PER MODE
    #ESTABLISH FIELDS
    convergence_fields = ['mode', 'n', 'hit_rate']
    convergence_rows = []

    #CYCLE THROUGH AND APPEND
    for mode in modes:
        for point in summary[mode]["convergence"]:
            convergence_rows.append({
                "mode"    : mode,
                "n"       : point["n"],
                "hit_rate": round(point["hit_rate"], 3),
            })

    #SAVE TO FILEPATH
    convergence_path = os.path.join(run_folder, "convergence.csv")
    _write_csv(convergence_path, convergence_fields, convergence_rows)

    #CONFIRM EXPORT TO USER
    print(f"\nCSV export complete: {run_folder}")
    print(f"  trial_data.csv      — {len(trial_rows)} rows")
    print(f"  summary_stats.csv   — {len(summary_rows)} rows")
    print(f"  motion_breakdown.csv— {len(motion_rows)} rows")
    print(f"  convergence.csv     — {len(convergence_rows)} rows")

    #OUTPUT DATA
    return run_folder