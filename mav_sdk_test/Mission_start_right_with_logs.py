# import asyncio
# import math
# from datetime import datetime
# from mavsdk import System
# from mavsdk.offboard import VelocityNedYaw, OffboardError
#
# LOG_FILE = "flight_log.txt"
#
# async def wait_for_altitude(drone, target_alt, percent=0.9):
#     threshold = target_alt * percent
#     print(f"[WAIT] Waiting for sonar to reach at least {threshold:.2f}m ({percent*100:.0f}% of target)...")
#     async for distance_sensor in drone.telemetry.distance_sensor():
#         sonar_alt = distance_sensor.current_distance_m
#         print(f"[SONAR] Altitude: {sonar_alt:.2f}m")
#         if sonar_alt >= threshold:
#             print(f"[REACHED] Sonar Altitude: {sonar_alt:.2f}m")
#             break
#
# async def print_telemetry(drone):
#     async for position in drone.telemetry.position():
#         print(f"[POS] Altitude: {position.relative_altitude_m:.2f}m")
#         break
#
# async def arm_and_takeoff(drone, altitude=2):
#     print("[ARMING]")
#     await drone.action.arm()
#     async for state in drone.telemetry.armed():
#         if state:
#             print("[INFO] Drone armed")
#             break
#     print(f"[TAKEOFF] Climbing to {altitude} meter")
#     await drone.action.set_takeoff_altitude(altitude)
#     await drone.action.takeoff()
#     await wait_for_altitude(drone, altitude)
#
#     # Start offboard mode
#     await drone.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0))
#     try:
#         await drone.offboard.start()
#         print("[OFFBOARD] Started")
#     except OffboardError as e:
#         print(f"[ERROR] Offboard start failed: {e._result.result}")
#         await drone.action.disarm()
#         return
#
# async def wait_until_disarmed(drone):
#     print("[WAIT] Waiting for drone to disarm...")
#     async for state in drone.telemetry.armed():
#         if not state:
#             print("[INFO] Drone disarmed")
#             break
#
# async def log_position(drone, stop_event, start_lat, start_lon, start_alt):
#     print("[LOGGER] Started logging position...")
#     async for position in drone.telemetry.position():
#         timestamp = datetime.utcnow().isoformat()
#         mean_lat_rad = math.radians((position.latitude_deg + start_lat) / 2.0)
#         delta_x = (position.latitude_deg - start_lat) * 111320
#         delta_y = (position.longitude_deg - start_lon) * (40075000 * math.cos(mean_lat_rad) / 360)
#         delta_z = position.relative_altitude_m - start_alt
#
#         line = f"{timestamp} | X: {delta_x:.2f} m, Y: {delta_y:.2f} m, Z: {delta_z:.2f} m\n"
#         with open(LOG_FILE, "a") as f:
#             f.write(line)
#
#         await asyncio.sleep(2)
#         if stop_event.is_set():
#             print("[LOGGER] Stopped logging position.")
#             break
#
# async def move_with_telemetry(drone, velocity_ned, duration_s):
#     await drone.offboard.set_velocity_ned(velocity_ned)
#     for _ in range(duration_s):
#         await print_telemetry(drone)
#         await asyncio.sleep(1)
#
# async def hold(drone, duration_s=3):
#     print(f"[HOLD] Holding position for {duration_s}s")
#     await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, 0.0))
#     await asyncio.sleep(duration_s)
#
# async def run():
#     drone = System(mavsdk_server_address="localhost", port=50051)
#     await drone.connect()
#
#     print("[INFO] Connecting...")
#     async for state in drone.core.connection_state():
#         if state.is_connected:
#             print("[INFO] Drone connected")
#             break
#
#     # Overwrite the log file at mission start
#     with open(LOG_FILE, "w") as f:
#         f.write(f"=== Mission Log Started at {datetime.utcnow().isoformat()} ===\n")
#
#     checkpoints = [
#         ("Checkpoint 1", VelocityNedYaw(0.19, -0.54, 0.0, 0.0), 10),
#         ("Checkpoint 2", VelocityNedYaw(0.6, 0.05, 0.0, 0.0), 10),
#         ("Checkpoint 3", VelocityNedYaw(-0.1, 0.4, 0.0, 0.0), 10),
#     ]
#
#     global_start_lat = None
#     global_start_lon = None
#     global_start_alt = None
#
#     for idx, (label, velocity, duration) in enumerate(checkpoints, start=1):
#         print(f"\n==== {label} ====")
#         await arm_and_takeoff(drone)
#
#         # Record start position
#         async for pos in drone.telemetry.position():
#             start_lat = pos.latitude_deg
#             start_lon = pos.longitude_deg
#             start_alt = pos.relative_altitude_m
#
#             if global_start_lat is None:
#                 global_start_lat = start_lat
#                 global_start_lon = start_lon
#                 global_start_alt = start_alt
#
#             print("[LOGGER] Start position recorded")
#             break
#
#         # Start logger
#         stop_event = asyncio.Event()
#         log_task = asyncio.create_task(
#             log_position(drone, stop_event, start_lat, start_lon, start_alt)
#         )
#
#         print(f"[MOVE] {label}")
#         await move_with_telemetry(drone, velocity, duration)
#         await hold(drone, 1)
#
#         # Log checkpoint
#         timestamp = datetime.utcnow().isoformat()
#         with open(LOG_FILE, "a") as f:
#             f.write(f"CHECKPOINT {idx} REACHED at {timestamp}\n")
#
#         try:
#             await drone.offboard.stop()
#             print("[OFFBOARD] Stopped")
#         except OffboardError as e:
#             print(f"[WARN] Offboard stop failed: {e._result.result}")
#
#         # Land
#         await drone.action.land()
#         await asyncio.sleep(3)
#         await wait_until_disarmed(drone)
#
#         # Stop logger
#         stop_event.set()
#         await log_task
#
#         # Log final position and cumulative displacement
#         async for pos in drone.telemetry.position():
#             # Relative to this checkpoint takeoff
#             mean_lat_rel = math.radians((pos.latitude_deg + start_lat) / 2.0)
#             delta_x_rel = (pos.latitude_deg - start_lat) * 111320
#             delta_y_rel = (pos.longitude_deg - start_lon) * (40075000 * math.cos(mean_lat_rel) / 360)
#             delta_z_rel = pos.relative_altitude_m - start_alt
#
#             timestamp = datetime.utcnow().isoformat()
#             with open(LOG_FILE, "a") as f:
#                 f.write(
#                     f"LAND (relative): X={delta_x_rel:.2f} m, Y={delta_y_rel:.2f} m, Z={delta_z_rel:.2f} m at {timestamp}\n"
#                 )
#
#             # Cumulative from global mission start
#             mean_lat_cum = math.radians((pos.latitude_deg + global_start_lat) / 2.0)
#             delta_x_cum = (pos.latitude_deg - global_start_lat) * 111320
#             delta_y_cum = (pos.longitude_deg - global_start_lon) * (40075000 * math.cos(mean_lat_cum) / 360)
#             delta_z_cum = pos.relative_altitude_m - global_start_alt
#
#             with open(LOG_FILE, "a") as f:
#                 f.write(
#                     f"CUMULATIVE DISPLACEMENT FROM MISSION START:\n"
#                     f"X={delta_x_cum:.2f} m, Y={delta_y_cum:.2f} m, Z={delta_z_cum:.2f} m\n"
#                 )
#
#             print("[LOGGER] Cumulative displacement logged")
#             break
#
# if __name__ == "__main__":
#     asyncio.run(run())
#
#

import asyncio
import math
import requests
from datetime import datetime
from mavsdk import System
from mavsdk.offboard import VelocityNedYaw, OffboardError

LOG_FILE = "flight_log.txt"

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

async def wait_until_disarmed(drone):
    print("[WAIT] Waiting for drone to disarm...")
    async for state in drone.telemetry.armed():
        if not state:
            print("[INFO] Drone disarmed")
            break

async def land_command_listener(drone, stop_flag):
    print("[LISTENER] Land listener started...")
    while not stop_flag.is_set():
        try:
            response = requests.get("http://localhost:8000/land_status")
            if response.ok and response.text.strip() == "LAND":
                print("[LISTENER] Land signal received! Initiating landing...")
                try:
                    await drone.offboard.stop()
                    print("[OFFBOARD] Stopped before landing.")
                except Exception as e:
                    print(f"[OFFBOARD] Already stopped or failed to stop: {e}")
                await drone.action.land()
                await asyncio.sleep(3)
                await wait_until_disarmed(drone)

                reset_response = requests.post("http://localhost:8000/reset_land")
                if reset_response.ok:
                    print("[LISTENER] Land status reset successfully on server.")
                else:
                    print(f"[LISTENER] Failed to reset land status (HTTP {reset_response.status_code})")

        except Exception as e:
            print(f"[LISTENER] Error: {e}")
        await asyncio.sleep(1)

async def log_position(drone, stop_event, start_lat, start_lon, start_alt):
    print("[LOGGER] Started logging position...")
    async for position in drone.telemetry.position():
        timestamp = datetime.utcnow().isoformat()
        mean_lat_rad = math.radians((position.latitude_deg + start_lat) / 2.0)
        delta_x = (position.latitude_deg - start_lat) * 111320
        delta_y = (position.longitude_deg - start_lon) * (40075000 * math.cos(mean_lat_rad) / 360)
        delta_z = position.relative_altitude_m - start_alt

        line = f"{timestamp} | X: {delta_x:.2f} m, Y: {delta_y:.2f} m, Z: {delta_z:.2f} m\n"
        with open(LOG_FILE, "a") as f:
            f.write(line)

        await asyncio.sleep(2)
        if stop_event.is_set():
            print("[LOGGER] Stopped logging position.")
            break

async def move_with_telemetry(drone, velocity_ned, duration_s):
    await drone.offboard.set_velocity_ned(velocity_ned)
    for _ in range(duration_s):
        await print_telemetry(drone)
        await asyncio.sleep(1)

async def hold(drone, duration_s=3):
    print(f"[HOLD] Holding position for {duration_s}s")
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, 0.0))
    await asyncio.sleep(duration_s)

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

    # Overwrite the log file at mission start
    with open(LOG_FILE, "w") as f:
        f.write(f"=== Mission Log Started at {datetime.utcnow().isoformat()} ===\n")

    checkpoints = [
                ("Checkpoint 1", VelocityNedYaw(0.54, 0.19, 0.0, 0.0), 10),
                ("Checkpoint 2", VelocityNedYaw(-0.2, 0.6, 0.0, 0.0), 10),
                ("Checkpoint 3", VelocityNedYaw(-0.2, -0.1, 0.0, 0.0), 10),
                ("Home", VelocityNedYaw(-0.09, -0.69, 0.0, 0.0), 10),
    ]

    global_start_lat = None
    global_start_lon = None
    global_start_alt = None

    stop_flag = asyncio.Event()
    listener_task = asyncio.create_task(land_command_listener(drone, stop_flag))

    try:
        for idx, (label, velocity, duration) in enumerate(checkpoints, start=1):
            print(f"\n==== {label} ====")
            await arm_and_takeoff(drone)

            # Record start position
            async for pos in drone.telemetry.position():
                start_lat = pos.latitude_deg
                start_lon = pos.longitude_deg
                start_alt = pos.relative_altitude_m

                if global_start_lat is None:
                    global_start_lat = start_lat
                    global_start_lon = start_lon
                    global_start_alt = start_alt

                print("[LOGGER] Start position recorded")
                break

            # Start logger
            stop_event = asyncio.Event()
            log_task = asyncio.create_task(
                log_position(drone, stop_event, start_lat, start_lon, start_alt)
            )

            print(f"[MOVE] {label}")
            vx_fwd, vy_fwd = rotate_velocity_ned(velocity.north_m_s, velocity.east_m_s, heading_deg)
            velocity = VelocityNedYaw(vx_fwd, vy_fwd, 0.0, 0.0)
            await move_with_telemetry(drone, velocity, duration)
            await hold(drone, 1)

            # Log checkpoint
            timestamp = datetime.utcnow().isoformat()
            with open(LOG_FILE, "a") as f:
                f.write(f"CHECKPOINT {idx} REACHED aat {timestamp}\n")

            try:
                await drone.offboard.stop()
                print("[OFFBOARD] Stopped")
            except OffboardError as e:
                print(f"[WARN] Offboard stop failed: {e._result.result}")

            # Land
            await drone.action.land()
            await asyncio.sleep(2)
            await wait_until_disarmed(drone)

            # Stop logger
            stop_event.set()
            await log_task

            # Log final position and cumulative displacement
            async for pos in drone.telemetry.position():
                # Relative to this checkpoint takeoff
                mean_lat_rel = math.radians((pos.latitude_deg + start_lat) / 2.0)
                delta_x_rel = (pos.latitude_deg - start_lat) * 111320
                delta_y_rel = (pos.longitude_deg - start_lon) * (40075000 * math.cos(mean_lat_rel) / 360)
                delta_z_rel = pos.relative_altitude_m - start_alt

                timestamp = datetime.utcnow().isoformat()
                with open(LOG_FILE, "a") as f:
                    f.write(
                        f"LAND (relative): X={delta_x_rel:.2f} m, Y={delta_y_rel:.2f} m, Z={delta_z_rel:.2f} m at {timestamp}\n"
                    )

                # Cumulative from global mission start
                mean_lat_cum = math.radians((pos.latitude_deg + global_start_lat) / 2.0)
                delta_x_cum = (pos.latitude_deg - global_start_lat) * 111320
                delta_y_cum = (pos.longitude_deg - global_start_lon) * (40075000 * math.cos(mean_lat_cum) / 360)
                delta_z_cum = pos.relative_altitude_m - global_start_alt

                with open(LOG_FILE, "a") as f:
                    f.write(
                        f"CUMULATIVE DISPLACEMENT FROM MISSION START:\n"
                        f"X={delta_x_cum:.2f} m, Y={delta_y_cum:.2f} m, Z={delta_z_cum:.2f} m\n"
                    )

                print("[LOGGER] Cumulative displacement logged")
                break
    finally:
        stop_flag.set()
        await listener_task


if __name__ == "__main__":
    asyncio.run(run())
