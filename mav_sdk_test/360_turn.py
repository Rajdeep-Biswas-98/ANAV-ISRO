import asyncio
from mavsdk import System
from mavsdk.offboard import VelocityNedYaw, OffboardError

async def print_telemetry(drone):
    async for position in drone.telemetry.position():
        print(f"[POS] Altitude: {position.relative_altitude_m:.2f}m")
        break

# async def wait_for_altitude(drone, target_alt, margin=0.1):
#     print(f"[WAIT] Waiting to reach {target_alt}m altitude...")
#     async for position in drone.telemetry.position():
#         if abs(position.relative_altitude_m - target_alt) <= margin:
#             print(f"[REACHED] Altitude: {position.relative_altitude_m:.2f}m")
#             break

async def wait_for_altitude(drone, target_alt, percent=0.9):
    threshold = target_alt * percent
    print(f"[WAIT] Waiting for sonar to reach at least {threshold:.2f}m ({percent*100:.0f}% of target)...")
    async for distance_sensor in drone.telemetry.distance_sensor():
        sonar_alt = distance_sensor.current_distance_m
        print(f"[SONAR] Altitude: {sonar_alt:.2f}m")
        if sonar_alt >= threshold:
            print(f"[REACHED] Sonar Altitude: {sonar_alt:.2f}m")
            break

async def run():
    drone = System(mavsdk_server_address="localhost", port=50051)
    await drone.connect()

    # Wait for connection
    print("[INFO] Connecting...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("[INFO] Drone connected")
            break

    # Arm the drone
    print("[ARMING]")
    await drone.action.arm()
    async for state in drone.telemetry.armed():
        if state:
            print("[INFO] Drone armed")
            break

    # Set takeoff altitude
    print("[TAKEOFF] Climbing to 1.5 meter")
    await drone.action.set_takeoff_altitude(1.5)
    await drone.action.takeoff()
    await wait_for_altitude(drone, 1.5)

    # Start offboard mode
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0))
    try:
        await drone.offboard.start()
        print("[OFFBOARD] Started")
    except OffboardError as e:
        print(f"[ERROR] Offboard start failed: {e._result.result}")
        await drone.action.disarm()
        return

    # Hover briefly before rotation
    print("[HOLD]")
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, 0.0))
    await asyncio.sleep(3)

    # Rotate 360 degrees slowly over ~5 seconds
    print("[ROTATING] Starting 360 degree turn")
    steps = 1      # Number of increments
    total_degrees = 360
    sleep_per_step = 1  # seconds
    degrees_per_step = total_degrees / steps

    yaw = 0.0
    for i in range(steps + 1):
        await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, yaw))
        print(f"[ROTATING] Yaw: {yaw:.1f} deg")
        yaw += degrees_per_step
        if yaw >= 360.0:
            yaw -= 360.0
        await asyncio.sleep(sleep_per_step)

    # print("[ROTATING] Starting 360 degree turn")
    # await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, 360))
    # await asyncio.sleep(5)

    

    # Hold a moment after completing rotation
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, yaw))
    await asyncio.sleep(2)

    # Land
    print("[LANDING]")
    await drone.action.land()
    await asyncio.sleep(5)

    # Disarm
    await drone.action.disarm()
    print("[DISARMED]")

if __name__ == "__main__":
    asyncio.run(run())
