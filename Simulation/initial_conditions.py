#Initial conditions for the simulation, including missile and interceptor parameters, and environmental conditions.
import math
import serial
import time
#INITIAL HEADING FUNCTION
def read_gimball_angles():
    try:
        #OPEN SERIAL PORT AND READ DATA
        ser = serial.Serial('COM4', 115200, timeout=1)
        time.sleep(2)  # WAIT FOR SERIAL CONNECTION TO ESTABLISH
        ser.write(b"r")#REQUEST ANGLES
        line = ser.readline().decode().strip()
        yaw_deg, pitch_deg = map(float, line.split())
#Interceptor parameters
Vi = float(input("Enter an interceptor speed (m/s): "))
yaw_rad, pitch_rad = read_gimball_angles() #MAKE THIS FUNCTION STILL

