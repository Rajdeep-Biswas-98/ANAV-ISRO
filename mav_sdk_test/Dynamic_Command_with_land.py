# import asyncio, requests, threading
# from mavsdk import System
# from mavsdk.offboard import VelocityNedYaw, OffboardError
#
# async def print_telemetry(drone):
#     async for position in drone.telemetry.position():
#         print(f"[POS] Altitude: {position.relative_altitude_m:.2f}m")
#         break
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
# async def wait_until_disarmed(drone):
#     print("[WAIT] Waiting for drone to disarm...")
#     async for state in drone.telemetry.armed():
#         if not state:
#             print("[INFO] Drone disarmed")
#             break
#
# async def land_command_listener(drone, stop_flag):
#     print("[LISTENER] Land listener started...")
#     while not stop_flag.is_set():
#         try:
#             response = requests.get("http://localhost:8000/land_status")
#             if response.ok and response.text.strip() == "LAND":
#                 print("[LISTENER] Land signal received! Initiating landing...")
#                 try:
#                     await drone.offboard.stop()
#                     print("[OFFBOARD] Stopped before landing.")
#                 except Exception as e:
#                     print(f"[OFFBOARD] Already stopped or failed to stop: {e}")
#                 await drone.action.land()
#                 await asyncio.sleep(3)
#                 await wait_until_disarmed(drone)
#
#                 reset_response = requests.post("http://localhost:8000/reset_land")
#                 if reset_response.ok:
#                     print("[LISTENER] Land status reset successfully on server.")
#                 else:
#                     print(f"[LISTENER] Failed to reset land status (HTTP {reset_response.status_code})")
#
#         except Exception as e:
#             print(f"[LISTENER] Error: {e}")
#         await asyncio.sleep(1)
#
# async def run():
#     drone = System(mavsdk_server_address="localhost", port=50051)
#     await drone.connect()
#
#     # Wait for connection
#     print("[INFO] Connecting...")
#     async for state in drone.core.connection_state():
#         if state.is_connected:
#             print("[INFO] Drone connected")
#             break
#
#     # 🟢 Create the land listener stop flag and task
#     stop_flag = asyncio.Event()
#     listener_task = asyncio.create_task(land_command_listener(drone, stop_flag))
#
#     try:
#         # Arm the drone
#         print("[ARMING]")
#         await drone.action.arm()
#         async for state in drone.telemetry.armed():
#             if state:
#                 print("[INFO] Drone armed")
#                 break
#
#         # Set takeoff altitude
#         print("[TAKEOFF] Climbing to 1 meter")
#         await drone.action.set_takeoff_altitude(1.5)
#         await drone.action.takeoff()
#         await wait_for_altitude(drone, 1.5)
#
#         # Start offboard mode
#         await drone.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0))
#         try:
#             await drone.offboard.start()
#             print("[OFFBOARD] Started")
#         except OffboardError as e:
#             print(f"[ERROR] Offboard start failed: {e._result.result}")
#             await drone.action.disarm()
#             return
#
#         # Move forward
#         print("[MOVE] Forward 1m")
#         await drone.offboard.set_velocity_ned(VelocityNedYaw(0.5, 0.5, 0.0, 0.0))
#         for _ in range(3):
#             await print_telemetry(drone)
#             await asyncio.sleep(1)
#
#         # Hover
#         print("[HOLD]")
#         await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, 0.0))
#         await asyncio.sleep(1)
#
#         # Move right without yaw
#         print("[MOVE] Right 1m")
#         await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.5, 0.0, 0.0))
#         for _ in range(2):
#             await print_telemetry(drone)
#             await asyncio.sleep(1)
#
#         # # Move right with yaw 90.0°
#         # print("[MOVE] Right 1m with yaw 90.0°")
#         # await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.5, 0.0, 90.0))
#         # for _ in range(2):
#         #     await print_telemetry(drone)
#         #     await asyncio.sleep(1)
#
#         #First yaw then move forward
#         # print("[YAW] Yaw 90")
#         # await drone.offboard.set_velocity_ned(VelocityNedYaw(0.5, 0.0, 0.0, 90.0))
#         # await asyncio.sleep(2)
#         # print("[MOVE] Forward 1m")
#         # await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.5, 0.0, 0.0))
#         # for _ in range(3):
#         #     await print_telemetry(drone)
#         #     await asyncio.sleep(1)
#
#
#         # # Hover
#         # print("[HOLD]")
#         # await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, 0.0))
#         # await asyncio.sleep(2)
#
#         # Land
#         print("[LANDING]")
#         await drone.action.land()
#         await asyncio.sleep(10)
#
#         # # Disarm
#         # await drone.action.disarm()
#         # print("[DISARMED]")
#     finally:
#         stop_flag.set()
#         await listener_task
#
# if __name__ == "__main__":
#     asyncio.run(run())

import asyncio, requests, threading
from mavsdk import System
from mavsdk.offboard import VelocityNedYaw, OffboardError, VelocityBodyYawspeed


async def print_telemetry(drone):
    async for position in drone.telemetry.position():
        print(f"[POS] Altitude: {position.relative_altitude_m:.2f}m")
        break

async def wait_for_altitude(drone, target_alt, percent=0.9):
    threshold = target_alt * percent
    print(f"[WAIT] Waiting for sonar to reach at least {threshold:.2f}m ({percent*100:.0f}% of target)...")
    async for distance_sensor in drone.telemetry.distance_sensor():
        sonar_alt = distance_sensor.current_distance_m
        print(f"[SONAR] Altitude: {sonar_alt:.2f}m")
        if sonar_alt >= threshold:
            print(f"[REACHED] Sonar Altitude: {sonar_alt:.2f}m")
            break

async def wait_until_disarmed(drone):
    print("[WAIT] Waiting for drone to disarm...")
    async for state in drone.telemetry.armed():
        if not state:
            print("[INFO] Drone disarmed")
            break

async def arm_and_takeoff(drone, altitude=2):
    async for in_air in drone.telemetry.in_air():
        if in_air:
            print("[INFO] Drone is already in air. Skipping takeoff.")
            return  # Just return without taking off
        else:
            break
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
    # await drone.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0))
    await drone.offboard.set_velocity_body(VelocityBodyYawspeed(forward_m_s=0.5, right_m_s=0.0, down_m_s=0.0, yawspeed_deg_s=0.0))
    try:
        await drone.offboard.start()
        print("[OFFBOARD] Started")
    except OffboardError as e:
        print(f"[ERROR] Offboard start failed: {e._result.result}")
        await drone.action.disarm()
        return

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

async def move_with_telemetry(drone, velocity_ned, duration_s):
    await drone.offboard.set_velocity_ned(velocity_ned)
    for _ in range(duration_s):
        await print_telemetry(drone)
        await asyncio.sleep(1)

async def hold(drone, duration_s=3):
    print(f"[HOLD] Holding position for {duration_s}s")
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, 0.0))
    await asyncio.sleep(duration_s)

async def run():
    drone = System(mavsdk_server_address="localhost", port=50051)
    await drone.connect()

    # Wait for connection
    print("[INFO] Connecting...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("[INFO] Drone connected")
            break

    # Start listener
    stop_flag = asyncio.Event()
    listener_task = asyncio.create_task(land_command_listener(drone, stop_flag))

    # Mission steps
    mission_steps = [
        {"name": "1", "velocity": VelocityNedYaw(0.717, 0.219, 0.0, 0.0), "duration": 10},  # forward
        {"name": "2", "velocity": VelocityNedYaw(-0.124, 0.496, 0.0, 0.0), "duration": 10},  # right
        {"name": "3", "velocity": VelocityNedYaw(-0.717, -0.219, 0.0, 0.0), "duration": 10},  # backward
        {"name": "4", "velocity": VelocityNedYaw(-0.124, 0.496, 0.0, 0.0), "duration": 10},  # right
        {"name": "5", "velocity": VelocityNedYaw(0.717, 0.219, 0.0, 0.0), "duration": 10},  # forward
        {"name": "6", "velocity": VelocityNedYaw(-0.124, 0.496, 0.0, 0.0), "duration": 10},  # right
        {"name": "7", "velocity": VelocityNedYaw(-0.717, -0.219, 0.0, 0.0), "duration": 10},  # backward
        {"name": "8", "velocity": VelocityNedYaw(-0.124, 0.496, 0.0, 0.0), "duration": 10},  # right
        # {"name": "1", "velocity": VelocityNedYaw(0.755, 0.231, 0.0, 0.0), "duration": 10},  # forward
        # {"name": "2", "velocity": VelocityNedYaw(-0.130, 0.524, 0.0, 0.0), "duration": 10},  # right
        # {"name": "3", "velocity": VelocityNedYaw(-0.755, -0.231, 0.0, 0.0), "duration": 10},  # backward
        # {"name": "4", "velocity": VelocityNedYaw(-0.130, 0.524, 0.0, 0.0), "duration": 10},  # right
        # {"name": "5", "velocity": VelocityNedYaw(0.755, 0.231, 0.0, 0.0), "duration": 10},  # forward
        # {"name": "6", "velocity": VelocityNedYaw(-0.130, 0.524, 0.0, 0.0), "duration": 10},  # right
        # {"name": "7", "velocity": VelocityNedYaw(-0.755, -0.231, 0.0, 0.0), "duration": 10},  # backward
        # {"name": "8", "velocity": VelocityNedYaw(-0.130, 0.524, 0.0, 0.0), "duration": 10},  # right
    ]

    try:
        for idx, step in enumerate(mission_steps, start=1):
            # Arm and Takeoff
            await arm_and_takeoff(drone)

            velocity = step["velocity"]
            duration = step["duration"]

            print(f"[MOVE] {step['name']}")
            await move_with_telemetry(drone, velocity, duration)
            await hold(drone, 1)

            if step['name']== 'Backward':
                try:
                    await drone.offboard.stop()
                    print("[OFFBOARD] Stopped")
                except OffboardError as e:
                    print(f"[WARN] Offboard stop failed: {e._result.result}")

                # Land
                await drone.action.land()
                await asyncio.sleep(2)
                await wait_until_disarmed(drone)

    finally:
        stop_flag.set()
        await listener_task

if __name__ == "__main__":
    asyncio.run(run())