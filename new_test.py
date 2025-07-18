from dronekit import connect, VehicleMode
from pymavlink import mavutil
import time
import logging

logging.basicConfig(level=logging.INFO)

def arm_vehicle(vehicle):
    # logging.info("Disabling pre-arm checks")
    # vehicle.parameters['ARMING_CHECK'] = 0
    # time.sleep(1)

    logging.info("Setting mode to GUIDED")
    vehicle.mode = VehicleMode("GUIDED")
    while not vehicle.mode.name == 'GUIDED':
        logging.info(f" Waiting for GUIDED mode: {vehicle.mode.name}")
        time.sleep(1)

    vehicle.armed = True
    while not vehicle.armed:
        logging.info(" Waiting for arming...")
        time.sleep(3)
    logging.info("Vehicle armed!")

def main():
    # If you want to use UDP (SITL)
    connection_string: str = 'udp:127.0.0.1:14551'
    # If you want serial instead, uncomment below and comment out the UDP line
    # connection_string = 'com8'
    # baud_rate = 57600

    logging.info(f"Connecting to vehicle on: {connection_string}")
    vehicle = connect(connection_string, wait_ready=True, timeout=60)
    # For serial connection:
    # vehicle = connect(connection_string, wait_ready=True, baud=baud_rate, timeout=60)

    try:
        arm_vehicle(vehicle)

        # Take off to 1 meter
        target_altitude = 1
        logging.info(f"Taking off to {target_altitude} meter")
        vehicle.simple_takeoff(target_altitude)

        # Wait until the vehicle reaches target altitude
        while True:
            current_alt = vehicle.location.global_relative_frame.alt
            logging.info(f" Altitude: {current_alt:.2f} m")
            if current_alt >= target_altitude * 0.95:
                logging.info("Reached target altitude")
                break
            time.sleep(1)

        # Hover for 5 seconds
        logging.info("Hovering for 5 seconds...")
        time.sleep(5)

        # Land
        logging.info("Landing")
        vehicle.mode = VehicleMode("LAND")
        while not vehicle.mode.name == 'LAND':
            logging.info(" Waiting for LAND mode...")
            time.sleep(1)

        # Wait until disarmed
        while vehicle.armed:
            logging.info(" Waiting for disarming...")
            time.sleep(1)

        logging.info("Landed and disarmed")

    finally:
        logging.info("Closing connection")
        vehicle.close()

if __name__ == "__main__":
    main()