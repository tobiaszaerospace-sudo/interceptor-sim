import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation
import numpy as np
from matplotlib.patches import Patch

# 3D ORIENTATION FROM VELOCITY
def orientation_from_velocity(v):
    #NORMAL IS NOW THE FORWARD DIRECTION
    fwd = v / (np.linalg.norm(v) + 1e-9)

    #WORLD UP VECTOR
    world_up = np.array([0,0,1])

    #RIGHT VECTOR
    right = np.cross(world_up, fwd)
    right /= (np.linalg.norm(right) + 1e-9)

    #COMPUTE TRUE UP VECTOR
    up = np.cross(fwd, right)

    #ROTATION MATRIX COLUMNS (RIGHT, UP, FORWARD)
    R = np.column_stack((right, up, fwd))
    return R


#PLOTTING FUNCTION FOR THE 3D TRAJECTORY
def plot_3d_trajectory(history, kill_radius):

    #GRAB POSITIONS
    xi = np.array([step["interceptor_pos"] for step in history])
    xt = np.array([step["target_pos"] for step in history])

    #GRAB VELOCITIES
    vi = np.array([step["interceptor_vel"] for step in history])
    vt = np.array([step["target_vel"] for step in history])

    #TIME STEP
    t_vals = [step["t"] for step in history]

    #MISSILE SHAPED MARKER FOR ANIMATION
    missile_shape = np.array([
        [0,0,1.5],  #NOSE
        [-.3,0,-1], #LEFT FIIN
        [.3,0,-1],  #RIGHT FIN
        [0,0,-1]    #TAIL
    ])

    #INITIALIZE PLOTTING WINDOW
    fig = plt.figure()
    panel = fig.add_subplot(111, projection='3d')

    #PLOT INTERCEPTOR AND TARGET (FAINT FOR PRE-ANIMATION)
    panel.plot(xi[:,0], xi[:,1], xi[:,2], color = "blue", alpha = 0.2)
    panel.plot(xt[:,0], xt[:,1], xt[:,2], color = "red", alpha = .2)

    #MISSILE BODIES AS LINE3D OBJECTS
    interceptor_body, = panel.plot([], [], [], color = "blue", linewidth = 2)
    target_body, = panel.plot([], [], [], color = "red", linewidth = 2)

    #TIME TEXT IN TOP CORNER
    time_text = panel.text(0.95, 0.95, 0, "", ha = "right", va = "top", fontsize = 12)

    #SET LABELS 
    panel.set_xlabel("X (m)")
    panel.set_ylabel("Y (m)")
    panel.set_zlabel("Z (m)")
    panel.set_title("3D Trajectory")

    #EQUAL ASPECT RATIO (FOV)
    all_pts = np.vstack((xi,xt))
    max_range = (all_pts.max(axis=0) - all_pts.min(axis=0)).max()
    mid = all_pts.mean(axis=0)
    panel.set_xlim(mid[0] - max_range/2, mid[0] + max_range/2)
    panel.set_ylim(mid[1] - max_range/2, mid[1] + max_range/2)
    panel.set_zlim(mid[2] - max_range/2, mid[2] + max_range/2)

    #SPHERE MESH
    u,v = np.mgrid[0:2*np.pi:40j, 0:np.pi:20j]
    xs = kill_radius * np.cos(u)*np.sin(v)
    ys = kill_radius * np.sin(u) * np.sin(v)
    zs = kill_radius * np.cos(v)

    #INITIAL SPHERE
    sphere = panel.plot_surface(xs + xt[0,0],
                       ys + xt[0,1],
                       zs + xt[0,2],
                       color="yellow", alpha=0.35, label = "_nolegend_")
    
    legend_elements = [plt.Line2D([0], [0], color='blue', lw=2, label='Interceptor'),
                          plt.Line2D([0], [0], color='red', lw=2, label='Target'),
                          Patch(facecolor='yellow', edgecolor='yellow', alpha=0.5, label=f'Kill Radius ({kill_radius} m)')]
    panel.legend(handles=legend_elements, loc='upper left')

    #ANIMATION UPDATE FUNCTION
    def update(i):
        nonlocal sphere

        #REMOVE OLE SPHERE
        sphere.remove()

        #DRAW A NEW SPHERE CENTERED AT TARGET POSITION
        sphere = panel.plot_surface(xs+xt[i,0],
                                    ys + xt[i,1],
                                    zs + xt[i,2],
                                    color = "yellow", alpha = .15)

        #INTERCEPTOR ORIENTATION
        Rotation_i = orientation_from_velocity(vi[i])
        missile_i = (Rotation_i @ missile_shape.T).T + xi[i]
        interceptor_body.set_data_3d(missile_i[:,0],
                                     missile_i[:,1],
                                     missile_i[:,2])
        
        #TARGET ORIENTATION
        Rotation_t = orientation_from_velocity(vt[i])
        missile_t = (Rotation_t @ missile_shape.T).T + xt[i]
        target_body.set_data_3d(missile_t[:,0],
                                     missile_t[:,1],
                                     missile_t[:,2])
        
        #TIME TEXT
        time_text.set_text(f"t = {t_vals[i]:.2f} s")

        return interceptor_body, target_body, time_text, sphere

    #RUN ANIMATION
    anim = FuncAnimation(fig, update, frames = len(history), interval = 30, blit = False)

    #SHOW IT CLEANLY
    plt.tight_layout()
    plt.show()