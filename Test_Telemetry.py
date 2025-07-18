from dronekit import connect, VehicleMode, LocationGlobalRelative
import time
import math
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

def arm_and_takeoff(vehicle, target_altitude):
    # print("Disabling pre-arm checks to force arm")
    # vehicle.parameters['ARMING_CHECK'] = 0  # Disable pre-arm checks

    print("Arming motors")
    vehicle.mode = VehicleMode("STABILIZE")
    vehicle.armed = True

    while not vehicle.armed:
        print(" Waiting for arming...")
        time.sleep(1)

    # print(f"Taking off to {target_altitude} meters")
    # vehicle.simple_takeoff(target_altitude)
    #
    # while True:
    #     alt = vehicle.location.global_relative_frame.alt
    #     print(f" Altitude: {alt:.2f} m")
    #     if alt >= target_altitude * 0.95:
    #         print("Reached target altitude")
    #         break
    #     time.sleep(1)

def get_location_metres(original_location, dNorth, dEast):
    """
    Returns a LocationGlobalRelative object offset by dNorth and dEast meters.
    """
    earth_radius = 6378137.0  # Radius of the earth in meters

    dLat = dNorth / earth_radius
    dLon = dEast / (earth_radius * math.cos(math.pi * original_location.lat / 180))

    newlat = original_location.lat + (dLat * 180 / math.pi)
    newlon = original_location.lon + (dLon * 180 / math.pi)
    return LocationGlobalRelative(newlat, newlon, original_location.alt)

def goto_position(vehicle, north, east, down):
    """
    Move vehicle to a position relative to home (NED: North, East, Down)
    """
    # Wait for home location
    while not vehicle.home_location:
        print("Waiting for home location...")
        cmds = vehicle.commands
        cmds.download()
        cmds.wait_ready()
        time.sleep(1)

    home_location = vehicle.home_location
    print(f"Home location acquired: {home_location}")

    target_location = get_location_metres(home_location, north, east)
    target_altitude = home_location.alt - down

    target = LocationGlobalRelative(target_location.lat, target_location.lon, target_altitude)
    print(f"Going to N:{north} E:{east} Alt:{target_altitude}")
    vehicle.simple_goto(target)

def main():
    connection_string = 'udp:127.0.0.1:14551'
    print(f"Connecting to vehicle on: {connection_string}")
    try:
        vehicle = connect(connection_string, wait_ready=True, timeout=60)
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    # try:
    #     # Arm and take off
    #     arm_and_takeoff(vehicle, 1)
    #     time.sleep(3)
    #
    #     # Square mission (1m steps)
    #     square_size = 5
    #     points = [
    #         (square_size, 0, 0),
    #         (square_size, square_size, 0),
    #         (0, square_size, 0),
    #         (0, 0, 0)
    #     ]
    #
    #     for north, east, down in points:
    #         goto_position(vehicle, north, east, down)
    #         time.sleep(10)

        print("Returning to Land Mode")
        vehicle.mode = VehicleMode("LAND")

    finally:
        print("Closing vehicle connection")
        vehicle.close()

if __name__ == "__main__":
    main()


