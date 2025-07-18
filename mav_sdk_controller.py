# mavsdk_guided_nogps_control.py

import asyncio
import sys
from mavsdk import System
from mavsdk.offboard import OffboardError, VelocityNedYaw


async def connect_drone(use_udp=True):
    if use_udp:
        print("[CONNECT] Connecting via UDP (telemetry)...")
        drone = System(mavsdk_server_address="localhost", port=50051)
        await drone.connect()
    else:
        print("[CONNECT] Connecting via SERIAL (/dev/ttyACM0)...")
        drone = System()
        await drone.connect(system_address="serial:///dev/ttyACM0:57600")

    # Wait until connected
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("[INFO] Drone connected!")
            break
    return drone


async def arm_and_start_offboard(drone):
    print("[ARM] Arming drone...")
    await drone.action.arm()
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0))
    try:
        await drone.offboard.start()
        print("[OFFBOARD] Started offboard control")
    except OffboardError as e:
        print(f"[ERROR] Offboard start failed: {e._result.result}")
        await drone.action.disarm()
        raise e


async def send_velocity(drone, vx, vy, vz, duration_sec):
    print(f"[MOVE] Velocity (vx={vx}, vy={vy}, vz={vz}) for {duration_sec}s")
    for _ in range(int(duration_sec * 10)):
        await drone.offboard.set_velocity_ned(VelocityNedYaw(vx, vy, vz, 0.0))
        await asyncio.sleep(0.1)


async def emergency_brake(drone):
    print("[BRAKE] Emergency stop")
    await send_velocity(drone, 0, 0, 0, 1)


async def main():
    use_udp = True  # Set to False if you want to use SERIAL USB
    drone = await connect_drone(use_udp)

    try:
        await arm_and_start_offboard(drone)

        # Ascend
        await send_velocity(drone, 0, 0, -0.5, 4)
        await emergency_brake(drone)
        await asyncio.sleep(2)

        # Move forward
        await send_velocity(drone, 0.5, 0, 0, 3)
        await emergency_brake(drone)
        await asyncio.sleep(2)

        # Move right
        await send_velocity(drone, 0, 0.5, 0, 3)
        await emergency_brake(drone)
        await asyncio.sleep(2)

        # Descend
        await send_velocity(drone, 0, 0, 0.5, 3)
        await emergency_brake(drone)
        await asyncio.sleep(2)

        # Land
        print("[LAND] Initiating landing...")
        await drone.action.land()
        await asyncio.sleep(10)

        print("[DISARM] Disarming...")
        await drone.action.disarm()
        print("[DONE]")

    finally:
        print("[CLOSE] Exiting script")


if __name__ == "__main__":
    asyncio.run(main())

#mavsdk_server_win32.exe udpin://127.0.0.1:14551 -p 50051