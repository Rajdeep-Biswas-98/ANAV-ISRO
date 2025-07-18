import asyncio
from mavsdk import System
from mavsdk.offboard import PositionNedYaw, OffboardError


async def wait_for_altitude(drone, target_alt, percent=0.9):
    threshold = target_alt * percent
    print(f"[WAIT] Waiting until sonar >= {threshold:.2f}m...")
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

    # Takeoff
    print("[TAKEOFF] Climbing to 1 meter")
    await drone.action.set_takeoff_altitude(1.0)
    await drone.action.takeoff()
    await wait_for_altitude(drone, 1.0)

    # Start Offboard with initial position hold
    initial_setpoint = PositionNedYaw(0.0, 0.0, -1.0, 0.0)
    await drone.offboard.set_position_ned(initial_setpoint)
    try:
        await drone.offboard.start()
        print("[OFFBOARD] Started (position control)")
    except OffboardError as e:
        print(f"[ERROR] Offboard start failed: {e._result.result}")
        await drone.action.disarm()
        return

    # Move forward 1 meter (North)
    print("[MOVE] Moving forward by 1 meter")
    await drone.offboard.set_position_ned(PositionNedYaw(
        1.0,   # North +1m
        0.0,   # East 0m
        -1.0,  # Altitude 1m above home
        0.0    # Yaw 0 degrees
    ))

    await asyncio.sleep(5)  # Allow time to reach

    # Hover
    print("[HOLD]")
    await drone.offboard.set_position_ned(PositionNedYaw(
        1.0, 0.0, -1.0, 0.0
    ))
    await asyncio.sleep(3)

    # Land
    print("[LANDING]")
    await drone.action.land()
    await asyncio.sleep(10)

    # Disarm
    await drone.action.disarm()
    print("[DISARMED]")


if __name__ == "__main__":
    asyncio.run(run())
