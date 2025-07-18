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

    # Start offboard mode
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0))
    try:
        await drone.offboard.start()
        print("[OFFBOARD] Started")
    except OffboardError as e:
        print(f"[ERROR] Offboard start failed: {e._result.result}")
        await drone.action.disarm()
        return

async def wait_until_disarmed(drone):
    print("[WAIT] Waiting for drone to disarm...")
    async for state in drone.telemetry.armed():
        if not state:
            print("[INFO] Drone disarmed")
            break

async def move_forward(drone, velocity_m_s=0.5, duration_s=3):
    print(f"[MOVE] Forward {velocity_m_s} m/s for {duration_s}s")
    await drone.offboard.set_velocity_ned(
        VelocityNedYaw(velocity_m_s, 0.0, 0.0, 0.0)
    )
    for _ in range(duration_s):
        await print_telemetry(drone)
        await asyncio.sleep(1)

async def move_backward(drone, velocity_m_s=0.5, duration_s=3):
    print(f"[MOVE] Backward {velocity_m_s} m/s for {duration_s}s")
    await drone.offboard.set_velocity_ned(
        VelocityNedYaw(-velocity_m_s, 0.0, 0.0, 0.0)
    )
    for _ in range(duration_s):
        await print_telemetry(drone)
        await asyncio.sleep(1)

async def move_right(drone, velocity_m_s=0.5, duration_s=3):
    print(f"[MOVE] Right {velocity_m_s} m/s for {duration_s}s")
    await drone.offboard.set_velocity_ned(
        VelocityNedYaw(0.0, velocity_m_s, 0.0, 0.0)
    )
    for _ in range(duration_s):
        await print_telemetry(drone)
        await asyncio.sleep(1)

async def move_left(drone, velocity_m_s=0.5, duration_s=3):
    print(f"[MOVE] Left {velocity_m_s} m/s for {duration_s}s")
    await drone.offboard.set_velocity_ned(
        VelocityNedYaw(0.0, -velocity_m_s, 0.0, 0.0)
    )
    for _ in range(duration_s):
        await print_telemetry(drone)
        await asyncio.sleep(1)


async def hold(drone, duration_s=3):
    print(f"[HOLD] Holding position for {duration_s}s")
    await drone.offboard.set_velocity_ned(
        VelocityNedYaw(0.0, 0.0, 0.0, 0.0)
    )
    await asyncio.sleep(duration_s)

async def run():
    num_iter=2
    drone = System(mavsdk_server_address="localhost", port=50051)
    await drone.connect()

    # Wait for connection
    print("[INFO] Connecting...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("[INFO] Drone connected")
            break

    for i in range(1,num_iter+1):
        if i%2==1:
            # === First Takeoff ===
            await arm_and_takeoff(drone)

            if i==num_iter:
                await move_forward(drone,0.5,3)
                await hold(drone,1)
                await drone.action.land()
                await asyncio.sleep(3)
                await wait_until_disarmed(drone)
            else:
                await move_forward(drone, 0.5, 3)
                await hold(drone, 1)
                await move_right(drone, 0.5, 3)
                await hold(drone, 1)
                await drone.action.land()
                await asyncio.sleep(3)
                await wait_until_disarmed(drone)

        else:
            # === First Takeoff ===
            await arm_and_takeoff(drone)

            if i==num_iter:
                await move_backward(drone, 0.5, 3)
                await hold(drone, 1)
                await drone.action.land()
                await asyncio.sleep(3)
                await wait_until_disarmed(drone)
            else:
                await move_backward(drone, 0.5, 3)
                await hold(drone, 1)
                await move_right(drone, 0.5, 3)
                await hold(drone, 1)
                await drone.action.land()
                await asyncio.sleep(3)
                await wait_until_disarmed(drone)

    # Returning to home position
    await arm_and_takeoff(drone)
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0))  # edit
    try:
        await drone.offboard.start()
        print("[OFFBOARD] Started")
    except OffboardError as e:
        print(f"[ERROR] Offboard start failed: {e._result.result}")
        await drone.action.disarm()
        return

    if num_iter%2==0:
        print(f"Returning to HOME position...")
        await move_left(drone, 0.5, 3*(num_iter-1))
        await hold(drone, 1)
        await drone.action.land()
        await asyncio.sleep(3)
    else:
        print(f"Returning to HOME position...")
        await move_left(drone, 0.5, 3 * (num_iter - 1))
        await hold(drone, 1)
        await move_backward(drone, 0.5, 3)
        await hold(drone, 1)
        await drone.action.land()
        await asyncio.sleep(3)


if __name__ == "__main__":
    asyncio.run(run())
