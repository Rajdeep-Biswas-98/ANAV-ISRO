import asyncio
from mavsdk import System
from mavsdk.offboard import VelocityBodyYawspeed, OffboardError

async def wait_for_altitude(drone, target_alt, percent=0.9):
    """
    Wait for the sonar to report at least target_alt * percent altitude.
    """
    threshold = target_alt * percent
    print(f"[WAIT] Waiting for sonar to reach {threshold:.2f}m...")
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

    # Arm
    print("[ARMING]")
    await drone.action.arm()
    async for state in drone.telemetry.armed():
        if state:
            print("[INFO] Drone armed")
            break

    # Takeoff
    takeoff_alt = 1.5
    print(f"[TAKEOFF] Climbing to {takeoff_alt}m")
    await drone.action.set_takeoff_altitude(takeoff_alt)
    await drone.action.takeoff()
    await wait_for_altitude(drone, takeoff_alt)

    # Start offboard mode with zero velocity
    await drone.offboard.set_velocity_body(VelocityBodyYawspeed(0, 0, 0, 0))
    try:
        await drone.offboard.start()
        print("[OFFBOARD] Started")
    except OffboardError as e:
        print(f"[ERROR] Offboard start failed: {e._result.result}")
        await drone.action.disarm()
        return

    # Hover briefly
    print("[HOLD]")
    await drone.offboard.set_velocity_body(VelocityBodyYawspeed(0, 0, 0, 0))
    await asyncio.sleep(2)

    # Rotate in place
    yaw_speed_deg_s = 20.0
    rotation_duration_s = 18  # Approx 360 / 20 = 18 sec
    print(f"[ROTATE] Rotating 360° at {yaw_speed_deg_s} deg/s")
    await drone.offboard.set_velocity_body(
        VelocityBodyYawspeed(
            forward_m_s=0.0,
            right_m_s=0.0,
            down_m_s=0.0,
            yawspeed_deg_s=yaw_speed_deg_s
        )
    )
    await asyncio.sleep(rotation_duration_s)

    # Stop rotation
    print("[STOP ROTATION]")
    await drone.offboard.set_velocity_body(VelocityBodyYawspeed(0, 0, 0, 0))
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
