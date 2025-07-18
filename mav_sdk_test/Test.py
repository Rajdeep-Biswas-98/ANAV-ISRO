import asyncio
import math
from mavsdk import System
from mavsdk.offboard import VelocityNedYaw, OffboardError

async def get_initial_heading(drone):
    async for euler in drone.telemetry.attitude_euler():
        heading_deg = euler.yaw_deg
        print(f"[INFO] Initial Heading (Yaw): {heading_deg:.2f}°")
        return heading_deg

def rotate_velocity_ned(vx, vy, heading_deg):
    theta = math.radians(heading_deg)
    new_vx = vx * math.cos(theta) - vy * math.sin(theta)
    new_vy = vx * math.sin(theta) + vy * math.cos(theta)
    return new_vx, new_vy

async def arm_and_takeoff(drone, altitude=2):
    print("[ARMING]")
    await drone.action.arm()
    async for state in drone.telemetry.armed():
        if state:
            print("[INFO] Drone armed")
            break
    print(f"[TAKEOFF] Climbing to {altitude} meter")
    await drone.action.set_takeoff_altitude(altitude)
    await drone.action.takeoff()
    await wait_for_altitude(drone, altitude)

async def wait_for_altitude(drone, target_alt, percent=0.95):
    threshold = target_alt * percent
    print(f"[WAIT] Waiting for sonar to reach at least {threshold:.2f}m ({percent*100:.0f}% of target)...")
    async for distance_sensor in drone.telemetry.distance_sensor():
        sonar_alt = distance_sensor.current_distance_m
        print(f"[SONAR] Altitude: {sonar_alt:.2f}m")
        if sonar_alt >= threshold:
            print(f"[REACHED] Sonar Altitude: cccccccccc{sonar_alt:.2f}m")
            break

async def wait_until_disarmed(drone):
    print("[WAIT] Waiting for drone to disarm...")
    async for state in drone.telemetry.armed():
        if not state:
            print("[INFO] Drone disarmed")
            break

async def run():
    drone = System(mavsdk_server_address="localhost", port=50051)
    await drone.connect()

    print("[INFO] Connecting...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("[INFO] Drone connected")
            break

    await arm_and_takeoff(drone)

    heading_deg = await get_initial_heading(drone)

    # Start offboard mode
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0))
    try:
        await drone.offboard.start()
        print("[OFFBOARD] Started")
    except OffboardError as e:
        print(f"[ERROR] Offboard start failed: {e._result.result}")
        await drone.action.disarm()
        return

    # Forward (relative to heading)
    vx_fwd, vy_fwd = rotate_velocity_ned(0.54, 0.19, heading_deg)
    print("[MOVE] 1st")
    await drone.offboard.set_velocity_ned(VelocityNedYaw(vx_fwd, vy_fwd, 0.0, 0.0))
    await asyncio.sleep(4)

    # Stop and hover
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0))
    await asyncio.sleep(2)

    print("[LANDING]")
    await drone.action.land()
    await asyncio.sleep(3)
    await wait_until_disarmed(drone)

    await arm_and_takeoff(drone)

    # Start offboard mode
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0))
    try:
        await drone.offboard.start()
        print("[OFFBOARD] Started")
    except OffboardError as e:
        print(f"[ERROR] Offboard start failed: {e._result.result}")
        await drone.action.disarm()
        return

    # # Backward (relative to heading)
    # vx_back, vy_back = rotate_velocity_ned(-0.2, 0.6, heading_deg)
    # print("[MOVE] 2nd")
    # await drone.offboard.set_velocity_ned(VelocityNedYaw(vx_back, vy_back, 0.0, 0.0))
    # await asyncio.sleep(4)
    #
    # # Stop and hover
    # await drone.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0))
    # await asyncio.sleep(2)
    #
    # print("[LANDING]")
    # await drone.action.land()
    # await asyncio.sleep(3)
    # await wait_until_disarmed(drone)
    #
    # await arm_and_takeoff(drone)
    #
    # # Start offboard mode
    # await drone.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0))
    # try:
    #     await drone.offboard.start()
    #     print("[OFFBOARD] Started")
    # except OffboardError as e:
    #     print(f"[ERROR] Offboard start failed: {e._result.result}")
    #     await drone.action.disarm()
    #     return
    #
    # # Backward (relative to heading)
    # vx_back, vy_back = rotate_velocity_ned(-0.2, -0.1, heading_deg)
    # print("[MOVE] 3rd")
    # await drone.offboard.set_velocity_ned(VelocityNedYaw(vx_back, vy_back, 0.0, 0.0))
    # await asyncio.sleep(4)
    #
    # # Stop and hover
    # await drone.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0))
    # await asyncio.sleep(2)
    #
    # print("[LANDING]")
    # await drone.action.land()
    # await asyncio.sleep(3)
    # await wait_until_disarmed(drone)
    #
    # await arm_and_takeoff(drone)
    #
    # # Start offboard mode
    # await drone.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0))
    # try:
    #     await drone.offboard.start()
    #     print("[OFFBOARD] Started")
    # except OffboardError as e:
    #     print(f"[ERROR] Offboard start failed: {e._result.result}")
    #     await drone.action.disarm()
    #     return
    #
    # # Backward (relative to heading)
    # vx_back, vy_back = rotate_velocity_ned(-0.09, -0.69, heading_deg)
    # print("[MOVE] HOME")
    # await drone.offboard.set_velocity_ned(VelocityNedYaw(vx_back, vy_back, 0.0, 0.0))
    # await asyncio.sleep(4)
    #
    # # Stop and hover
    # await drone.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0))
    # await asyncio.sleep(2)
    #
    # print("[LANDING]")
    # await drone.action.land()
    # await asyncio.sleep(3)
    # await wait_until_disarmed(drone)

if __name__ == "__main__":
    asyncio.run(run())