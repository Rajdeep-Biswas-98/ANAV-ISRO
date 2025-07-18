from pymavlink import mavutil
import time
import sys

# Connect to the autopilot on COM8 at 57600 baud
master = mavutil.mavlink_connection('udp:127.0.0.1:14550')

# Wait for the heartbeat message to confirm connection
master.wait_heartbeat()
print(f"Heartbeat from system {master.target_system} component {master.target_component}")

# Function to change flight mode
def change_mode(mode_name):
    if mode_name not in master.mode_mapping():
        print(f"Unknown mode: {mode_name}")
        print("Available modes:", list(master.mode_mapping().keys()))
        sys.exit(1)
    mode_id = master.mode_mapping()[mode_name]
    # Send the command to change mode
    master.mav.set_mode_send(
        master.target_system,
        mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
        mode_id)
    # Wait for ACK
    while True:
        ack = master.recv_match(type='COMMAND_ACK', blocking=True)
        if ack and ack.command == mavutil.mavlink.MAV_CMD_DO_SET_MODE:
            print(f"Mode change to {mode_name} result: {mavutil.mavlink.enums['MAV_RESULT'][ack.result].description}")
            break

# Function to arm the drone
def arm_drone():
    master.mav.command_long_send(
        master.target_system,
        master.target_component,
        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
        0,
        1, 0, 0, 0, 0, 0, 0)
    print("Arming motors...")
    master.motors_armed_wait()
    print("Motors armed!")

# Change mode to STABILIZE
change_mode('STABILIZE')

# Wait a bit before arming
time.sleep(2)

# Arm the drone (throttle on)
arm_drone()
