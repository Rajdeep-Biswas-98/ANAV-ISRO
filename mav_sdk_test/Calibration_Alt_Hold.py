import asyncio
from mavsdk import System
from mavsdk.offboard import VelocityNedYaw, OffboardError
from mavsdk.mavlink_passthrough import MavlinkPassthrough, MavlinkMessage
from pymavlink.dialects.v20 import common as mavlink2

async def calibrate_imu(drone):
    print("[CALIBRATION] Starting IMU (gyro+accel) calibration")
    mavlink = MavlinkPassthrough(drone)
    msg = mavlink2.MAVLink_command_long_message(
        target_system=1,
        target_component=1,
        command=mavlink2.MAV_CMD_PREFLIGHT_CALIBRATION,
        confirmation=0,
        param1=1, param2=1, param3=0, param4=0, param5=0, param6=0, param7=0
    )
    mav_msg = MavlinkMessage(msg.pack(mavlink2.MAVLink('', 2, 1)))
    mavlink.send_message(mav_msg)
    print("[CALIBRATION] IMU calibration command sent")
    await asyncio.sleep(10)

async def wait_for_altitude(drone, target_alt, margin=0.1):
    async for position in drone.telemetry.position():
        if abs(position.relative_altitude_m - target_alt) <= margin:
            print(f"[ALTITUDE] Reached {position.relative_altitude_m:.2f}m")
            break

async def hover(drone, seconds=3):
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0))
    print(f"[HOVER] Hovering for {seconds} seconds...")
    await asyncio.sleep(seconds)

async def move(drone, vx, vy, vz, duration, label=""):
    print(f"[MOVE] {label}: Vx={vx}, Vy={vy}, Vz={vz} for {duration}s")
    await drone.offboard.set_velocity_ned(VelocityNedYaw(vx, vy, vz, 0))
    await asyncio.sleep(duration)
    await hover(drone, 1)

async def run():
    drone = System(mavsdk_server_address="localhost", port=50051)
    await drone.connect()

    async for state in drone.core.connection_state():
        if state.is_connected:
            print("[CONNECTED] Drone connected")
            break

    await calibrate_imu(drone)

    await drone.action.arm()
    print("[ARMED]")

    await drone.action.set_takeoff_altitude(1.0)
    await drone.action.takeoff()
    await asyncio.sleep(5)
    await wait_for_altitude(drone, 1.0)

    await drone.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0))
    try:
        await drone.offboard.start()
        print("[OFFBOARD] Started")
    except OffboardError as e:
        print(f"[ERROR] {e._result.result}")
        await drone.action.disarm()
        return

    # Hover before moving
    await hover(drone, 2)

    # Move 1 meter forward (North) at 0.5 m/s for 2s
    await move(drone, 0.5, 0.0, 0.0, 2, "Forward 1m")

    # Move 1 meter backward (South) at 0.5 m/s for 2s
    await move(drone, -0.5, 0.0, 0.0, 2, "Backward 1m")

    # Hover before landing
    await hover(drone, 2)

    print("[LANDING]")
    await drone.action.land()
    await asyncio.sleep(8)
    await drone.action.disarm()
    print("[DISARMED]")

if __name__ == "__main__":
    asyncio.run(run())
