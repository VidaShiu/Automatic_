# Checking and compiling the provided script for syntax and logic errors.

import serial
import threading
import os
import time
import logging
import re

# Logging configuration
logging.basicConfig(
    filename='Raw_record.txt',
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Serial port configuration
serial_port = '/dev/ttyUSB0'
baud_rate = 115200
sends_command = "time_tick"
connected_response_pattern = r"\[time_tick\+ok\]\s*"  # RTC Response
correct_response = r"\[\*\+ok\]\s*"
reboot_finished = "POST Check - Coin Bat."  # Status-Reboot finished
file_upload_states = "File_TOTAL_CNT" # Status-File upload
lcm_homepage = "LCM State =  12" # Status-Device Idle

retry_times = 5  # Maximum retries for connection
reconnect_delay = 5  # Delay before retrying
response_timeout = 10  # Response wait timeout

stop_event = threading.Event()  # Event to signal stop


def clear_terminal_buffer():
    """Clear terminal buffer to prevent residual data."""
    print("Clearing terminal buffer...")
    os.system('clear')  # Clear for Unix/Linux/macOS

def establish_uart_connection(ser, connection_event):
    """Attempt to establish UART connection with retries."""
    for attempt in range(retry_times):
        try:
            clear_terminal_buffer()
            ser.write((sends_command + '\n').encode('utf-8'))
            print(f"Sent command: {sends_command}")

            start_time = time.time()
            while time.time() - start_time < response_timeout:
                if ser.in_waiting > 0:
                    response = ser.readline().decode('utf-8').strip()
                    print(f"Received from UATR: {response.strip()}")

                    if response == '>' or response == '':
                        continue

                    if re.match(connected_response_pattern, response):
                        print("UART communication successful!")
                        connection_event.set()  # Signal connection success
                        return True

            logging.info(f"Attempt {attempt + 1}/{retry_times} failed.")
            time.sleep(reconnect_delay)

        except serial.SerialException as e:
            logging.error(f"Serial communication error: {e}")
            time.sleep(reconnect_delay)

    logging.error(f"Failed to establish UART connection after {retry_times} attempts.")
    return False


def monitor_serial_port(connection_event, stop_event):
    reboot_detected = False
    file_upload_detected = False
    lcm_idle_detected = False
    sent_command_echo = None

    while not stop_event.is_set():
        ser = None
        try:
            ser = serial.Serial(serial_port, baud_rate, timeout=1)
            print(f"Connected to {serial_port} at {baud_rate} baud rate.")
            logging.info(f"Connected to {serial_port} at {baud_rate} baud rate.")

            if establish_uart_connection(ser, connection_event):
                last_clear_time = time.time()

                while not stop_event.is_set():
                    response = ""

                    if time.time() - last_clear_time >= 20:
                        clear_terminal_buffer()
                        last_clear_time = time.time()

                    if ser.in_waiting > 0:
                        response = ser.readline().decode('utf-8').strip()
                        
                        if response == '>' or response == '':
                            print(f"Ignored echoed command: {response.strip()}")
                            logging.info(f"Ignored echoed command: {response.strip()}")
                            continue

                        if not response or response == sent_command_echo:
                            print(f"Ignored echoed command: {response.strip()}")
                            logging.info(f"Ignored echoed command: {response.strip()}")
                            continue
                        
                        print(f"Received from UATR: {response.strip()}")
                        logging.info(f"Received from UATR: {response.strip()}")                  

                        if reboot_finished in response:
                            print("Reboot has been complete.")
                            logging.info("Reboot has been complete.")
                            reboot_detected = True

                        if file_upload_states in response:
                            print("File is Uploading.")
                            logging.info("File is Uploading.")
                            file_upload_detected = True

                        if lcm_homepage in response:
                            print("The device is idle.")
                            logging.info("The device is idle.")
                            lcm_idle_detected = True

                    # Check for disconnection or device idle state
                        if not connection_event.is_set():
                            logging.info("Communication failure detected, Reconnecting...")
                            break

                    time.sleep(1)

            connection_event.clear()
        except serial.SerialException as e:
            logging.error(f"Error opening serial port: {e}")
            time.sleep(reconnect_delay)

        finally:
            if ser and ser.is_open:
                ser.close()
                logging.info(f"Serial port {serial_port} closed.")
            time.sleep(reconnect_delay)

def classify_and_handle_response(response, condition_type):
    """Classify the response and handle it based on the condition type."""
    if condition_type == "asynchrony":
        handle_asynchrony(response)
    elif condition_type == "restore":
        handle_restore(response)
    elif condition_type == "therapy start":
        handle_therapy_start(response)
    elif condition_type == "therapy stop":
        handle_therapy_stop(response)
    else:
        logging.warning(f"Unknown condition type: {condition_type}")
        print(f"Unknown condition type: {condition_type}")

def handle_asynchrony(response):
    """Log and sort asynchronous responses."""
    with open("async_log.txt", "a") as file:
        file.write(f"{response}\n")
    print("Asynchronous response logged.")
    logging.info("Asynchronous response logged.")

def handle_restore(response):
    """Check if the response indicates a successful restore."""
    if "Reboot has been complete." in response:
        print("Restore successful.")
        logging.info("Restore successful.")
    else:
        print("Restore failed.")
        logging.warning("Restore failed.")

def handle_therapy_start(response):
    """Start a timer for therapy duration (example: 300 seconds)."""
    duration = 300  # Example duration; you can load it from Command_Line.yml if needed
    print(f"Therapy started. Duration: {duration} seconds.")
    logging.info(f"Therapy started for {duration} seconds.")
    time.sleep(duration)
    print("Therapy duration complete.")
    logging.info("Therapy duration complete.")

def handle_therapy_stop(response):
    """Check if the therapy stop response is valid."""
    if "File is Uploading." in response:
        print("Therapy stopped successfully.")
        logging.info("Therapy stopped successfully.")
    else:
        print("Therapy stop failed.")
        logging.warning("Therapy stop failed.")

if __name__ == '__main__':
    import sys
    connection_event = threading.Event()
    stop_event = threading.Event()

    try:
        # Start the serial port monitoring thread
        monitor_thread = threading.Thread(
            target=monitor_serial_port, 
            args=(connection_event, stop_event)
        )
        monitor_thread.start()

        print("Serial port monitoring initialized. Waiting for UART communication...")

        # Wait for connection establishment
        connection_event.wait(timeout=30)  # Timeout to prevent indefinite blocking
        if not connection_event.is_set():
            print("UART communication could not be established within timeout.")
            stop_event.set()
        else:
            print("UART communication successfully established.")

        # Monitor the stop event
        while not stop_event.is_set():
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nTerminating serial port monitoring due to keyboard interrupt.")
        logging.info("Serial monitoring terminated by user.")
        stop_event.set()

    except Exception as e:
        print(f"Error during execution: {e}")
        logging.error(f"Unexpected error: {e}")
        stop_event.set()

    finally:
        # Ensure the monitoring thread is properly terminated
        if monitor_thread.is_alive():
            stop_event.set()
            monitor_thread.join()

        print("Serial port monitoring stopped.")
        logging.info("Serial port monitoring stopped.")
        sys.exit(0)
