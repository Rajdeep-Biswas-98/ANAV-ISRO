import asyncio
from mavsdk import System
from mavsdk.offboard import VelocityNedYaw, OffboardError

async def wait_for_altitude(drone, target_alt, percent=0.9):
    threshold = target_alt * percent
    print(f"[WAIT] Waiting until sonar >= {threshold:.2f}m...")
    async for distance_sensor in drone.telemetry.distance_sensor():
        sonar_alt = distance_sensor.current_distance_m
        print(f"[SONAR] Altitude: {sonar_alt:.2f}m")
        if sonar_alt >= threshold:
            print(f"[REACHED] Sonar Altitude: {sonar_alt:.2f}m")
            break

async def hover(drone, seconds=3):
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0))
    print(f"[LOITER] Hovering for {seconds} seconds...")
    await asyncio.sleep(seconds)

async def move(drone, vx, vy, vz, duration, label=""):
    print(f"[MOVE] {label} for {duration}s → Vx:{vx}, Vy:{vy}, Vz:{vz}")
    await drone.offboard.set_velocity_ned(VelocityNedYaw(vx, vy, vz, 0.0))
    await asyncio.sleep(duration)
    await hover(drone)

async def run():
    drone = System(mavsdk_server_address="localhost", port=50051)
    await drone.connect()

    async for state in drone.core.connection_state():
        if state.is_connected:
            print("[CONNECTED] Drone connected")
            break

    await drone.action.arm()
    print("[ARMED]")

    await drone.action.set_takeoff_altitude(1.0)
    await drone.action.takeoff()
    await asyncio.sleep(5)
    await wait_for_altitude(drone, 1.0)

    await drone.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0))
    try:
        await drone.offboard.start()
        print("[OFFBOARD] Started")
    except OffboardError as e:
        print(f"[ERROR] {e._result.result}")
        await drone.action.disarm()
        return

    # Reference loiter
    print("[REFERENCE] Loitering at reference point")
    await hover(drone, 3)

    # Diagonal move (1m at 45° = 0.7, 0.7)
    await move(drone, 0.7, 0.7, 0, 2, "To diagonal vertex")

    # Square from diagonal vertex (1m edges at 0.5 m/s → 2s)
    await move(drone, 0.5, 0.0, 0, 2, "Edge 1 → forward")
    await move(drone, 0.0, -0.5, 0, 2, "Edge 2 → left")
    await move(drone, -0.5, 0.0, 0, 2, "Edge 3 → backward")
    await move(drone, 0.0, 0.5, 0, 2, "Edge 4 → right")

    # Return to reference (reverse of diagonal)
    await move(drone, -0.7, -0.7, 0, 2, "Return to reference point")

    # Final loiter
    print("[FINAL LOITER] Hovering before landing...")
    await hover(drone, 3)

    # Land
    print("[LANDING]")
    await drone.action.land()
    await asyncio.sleep(8)
    await drone.action.disarm()
    print("[DONE]")

if __name__ == "__main__":
    asyncio.run(run())
