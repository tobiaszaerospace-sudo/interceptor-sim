#IMPORT CLASSES
from Config.settings import Settings
from Simulation.simulate import run_simulation
from Visualization.plot_trajectory import plot_3d_trajectory

#NO NEED FOR CLASS, CAN JUST USE FUNCTION
def run_simulation(guidance_mode, motion_model, dt = ):
    #SHOW USER OPTIONS FOR GUIDANCE MODE
    print("\n=== Missiel Guidance Simulation ===")
    print("Choose guidance mode: ")
    print("1. Proportional Navigation (PN)")
    print("2. Augmented Proportional Navigation (APN)")
    print("3. Zero Effort Miss (ZEM)")
    print("4. Real Life Tracking Simulation")

