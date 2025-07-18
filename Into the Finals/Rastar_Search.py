import asyncio
import math
import requests
from mavsdk import System
from mavsdk.offboard import VelocityNedYaw, OffboardError

LOG_FILE = "Log.txt"

async def wait_for_altitude(drone, target_alt, percent=0.9):
    threshold = target_alt * percent
    print(f"[WAIT] Waiting for sonar to reach at least {threshold:.2f}m ({percent*100:.0f}% of target)...")
    async for distance_sensor in drone.telemetry.distance_sensor():
        sonar_alt = distance_sensor.current_distance_m
        print(f"[SONAR] Altitude: {sonar_alt:.2f}m")
        if sonar_alt >= threshold:
            print(f"[REACHED] Sonar Altitude: {sonar_alt:.2f}m")
            break

async def arm_and_takeoff(drone, altitude=3):
    print("[CHECK] Checking if drone is already armed...")

    # Check if drone is already armed
    is_already_armed = False
    async for state in drone.telemetry.armed():
        is_already_armed = state
        break  # We only need the latest state

    if is_already_armed:
        print("[WARNING] Drone is already armed. Skipping takeoff.")
        return

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

async def hold(drone, duration_s=2):
    print(f"[HOLD] Holding position for {duration_s}s")
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, 0.0))
    await asyncio.sleep(duration_s)

async def wait_until_disarmed(drone):
    print("[WAIT] Waiting for drone to disarm...")
    async for state in drone.telemetry.armed():
        if not state:
            print("[INFO] Drone disarmed")
            break

async def move_continuous(drone, velocity_ned):
    await drone.offboard.set_velocity_ned(velocity_ned)

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

async def run():
    drone = System(mavsdk_server_address="localhost", port=50051)
    await drone.connect()

    print("[INFO] Connecting...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("[INFO] Drone connected")
            break

    heading_deg = await get_initial_heading(drone)
    await arm_and_takeoff(drone)

    try:
        await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, 0.0))
        await drone.offboard.start()
        print("[OFFBOARD] Started")

        direction = "forward"
        land_count = 0

        while land_count < 3:
            # Determine velocity
            if direction == "forward":
                vx_fwd, vy_fwd = rotate_velocity_ned(0.3, 0.0, heading_deg)
                velocity = VelocityNedYaw(vx_fwd, vy_fwd, 0.0, 0.0)
                print("[MOVE] Moving forward")
            else:
                vx_bwd, vy_bwd = rotate_velocity_ned(-0.3, 0.0, heading_deg)
                velocity = VelocityNedYaw(vx_bwd, vy_bwd, 0.0, 0.0)
                print("[MOVE] Moving backward")

            await move_continuous(drone, velocity)

            while True:
                try:
                    # Check YELLOW
                    yellow_response = requests.get("http://localhost:8000/yellow_status")
                    if yellow_response.ok and yellow_response.text.strip() == "YELLOW":
                        print("[COMMAND] YELLOW signal received!")
                        await hold(drone, 1)

                        # Start right movement
                        vx_right, vy_right = rotate_velocity_ned(0.0, 0.3, heading_deg)
                        velocity_right = VelocityNedYaw(vx_right, vy_right, 0.0, 0.0)
                        print("[MOVE] Moving right 1 meter (up to 3.4s)")

                        right_start = asyncio.get_event_loop().time()
                        right_duration = 5

                        requests.post("http://localhost:8000/reset_yellow")

                        while True:
                            await move_continuous(drone, velocity_right)

                            yellow_check = requests.get("http://localhost:8000/yellow_status")
                            if yellow_check.ok and yellow_check.text.strip() == "YELLOW":
                                print("[COMMAND] YELLOW pressed during right movement - cancelling right move")
                                # STOP motion immediately
                                await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, 0.0))
                                await hold(drone, 1)
                                break

                            elapsed = asyncio.get_event_loop().time() - right_start
                            if elapsed >= right_duration:
                                print("[MOVE] Completed right movement (1m)")
                                await hold(drone, 1)
                                break

                            await asyncio.sleep(0.5)

                        # Toggle direction after right movement
                        direction = "backward" if direction == "forward" else "forward"

                        requests.post("http://localhost:8000/reset_yellow")
                        break  # exit inner loop to resume main loop

                    # Check LAND only in forward/backward movement
                    land_response = requests.get("http://localhost:8000/land_status")
                    if land_response.ok and land_response.text.strip() == "LAND":
                        print("[COMMAND] LAND signal received!")

                        try:
                            await drone.offboard.stop()
                            print("[OFFBOARD] Stopped before landing.")
                        except Exception as e:
                            print(f"[OFFBOARD] Already stopped or failed to stop: {e}")

                        await drone.action.land()
                        await wait_until_disarmed(drone)

                        land_count += 1
                        print(f"[COUNT] Land events handled: {land_count}/3")

                        if land_count != 3:
                            print("[PAUSE] Waiting 5 seconds before re-takeoff...")
                            await asyncio.sleep(5)
                            await arm_and_takeoff(drone)

                            await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, 0.0))
                            await drone.offboard.start()
                            print("[OFFBOARD] Restarted after landing.")

                        requests.post("http://localhost:8000/reset_land")
                        break  # back to main loop

                except Exception as e:
                    print(f"[ERROR] {e}")

                await asyncio.sleep(1)

        print("[MISSION] Land command triggered 3 times. Ending mission.")

    finally:
        print("[SHUTDOWN] Stopping offboard and landing")
        try:
            await drone.offboard.stop()
        except Exception:
            pass
        await drone.action.land()
        await wait_until_disarmed(drone)


if __name__ == "__main__":
    asyncio.run(run())