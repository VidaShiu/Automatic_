import logging
import serial
import time


class UARTCommunicator:
    """Handles UART communication with the device."""

    def __init__(self, port="/dev/ttyUSB0", baudrate=115200, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout

    def send_command(self, command):
        """Send a command and receive a response via UART."""
        try:
            with serial.Serial(port=self.port, baudrate=self.baudrate, timeout=self.timeout) as ser:
                ser.write(f"{command}\n".encode('utf-8'))
                logging.info(f"Sent command: {command}")
                time.sleep(1)
                return 
                
        except serial.SerialException as e:
            logging.error(f"UART Error: {e}")
            return None
    time.sleep(1)
