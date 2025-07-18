import asyncio
from mavsdk import System
from mavsdk.offboard import VelocityNedYaw, OffboardError

async def wait_for_altitude(drone, target_alt, percent=0.9):
    threshold = target_alt * percent
    print(f"[WAIT] Waiting for sonar to reach at least {threshold:.2f}m ({percent*100:.0f}% of target)...")
    async for distance_sensor in drone.telemetry.distance_sensor():
        sonar_alt = distance_sensor.current_distance_m
        print(f"[SONAR] Altitude: {sonar_alt:.2f}m")
        if sonar_alt >= threshold:
            print(f"[REACHED] Sonar Altitude: {sonar_alt:.2f}m")
            break

async def print_telemetry(drone):
    async for position in drone.telemetry.position():
        print(f"[POS] Altitude: {position.relative_altitude_m:.2f}m")
        break

async def arm_and_takeoff(drone, altitude=1.5):
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

async def run():
    drone = System(mavsdk_server_address="localhost", port=50051)
    await drone.connect()

    # Wait for connection
    print("[INFO] Connecting...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("[INFO] Drone connected")
            break
    # === First Takeoff ===
    await arm_and_takeoff(drone)

    # Start offboard mode
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0)) #edit
    try:
        await drone.offboard.start()
        print("[OFFBOARD] Started")
    except OffboardError as e:
        print(f"[ERROR] Offboard start failed: {e._result.result}")
        await drone.action.disarm()
        return

    # Move forward 1m
    print("[MOVE] Forward 1m")
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0.5, 0.0, 0.0, 0.0))
    for _ in range(3):
        await print_telemetry(drone)
        await asyncio.sleep(1)

    # Hover
    print("[HOLD]")
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, 0.0))
    await asyncio.sleep(3)

    # Land and disarm
    print("[LANDING]")
    await drone.action.land()
    await asyncio.sleep(3)
    # await drone.action.disarm()
    # print("[DISARMED]")

    # Wait 3 seconds
    print("[WAIT] Waiting 3 seconds before next mission...")
    await asyncio.sleep(3)

    # === Second Takeoff ===
    await arm_and_takeoff(drone)

    # Start offboard mode again
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0))
    try:
        await drone.offboard.start()
        print("[OFFBOARD] Started")
    except OffboardError as e:
        print(f"[ERROR] Offboard start failed: {e._result.result}")
        await drone.action.disarm()
        return

    # Move backward 1m
    print("[MOVE] Backward 1m")
    await drone.offboard.set_velocity_ned(VelocityNedYaw(-0.5, 0.0, 0.0, 0.0))
    for _ in range(3):
        await print_telemetry(drone)
        await asyncio.sleep(1)

    # Hover
    print("[HOLD]")
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, 0.0))
    await asyncio.sleep(3)

    # Land and disarm
    print("[LANDING]")
    await drone.action.land()
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, 0.0)) #edit
    await asyncio.sleep(5)
    # await drone.action.disarm()
    # print("[DISARMED]")

if __name__ == "__main__":
    asyncio.run(run())
