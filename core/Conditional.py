import re
import datetime
import yaml
import time
import logging


class Validator:
    def __init__(self, report_detail_file=f"Report_Detail_{datetime.datetime.now().strftime('%Y_%m_%d')}.txt"):
        """Initialize the validator with a report file for detailed test results."""
        self.report_detail_file = report_detail_file
        self.results = []

    def classify_data(self, response):
        """
        Split the response into prefix and actual_value.
        If no actual_value exists, return prefix only.
        """
        try:
            prefix, actual_value = response.split(" ", 1)
        except ValueError:
            prefix = response
            actual_value = None  # No actual value
        return prefix, actual_value

    def validate_data(self, condition, actual_value):
        condition_type = condition.get("type")
        expected_value = condition.get("expected")

        match condition_type:
            case "equal":
                return actual_value == expected_value
            case "between":
                low = int(condition.get("low", 0))
                high = int(condition.get("high", 0))
                return low <= int(actual_value) <= high
            case "timestamp":
                return self.is_valid_timestamp(actual_value)
            case "valid format_mac":
                return self.is_valid_mac_address(actual_value)
            case _:
                return False

    def is_valid_timestamp(self, actual_value):
        """Check if the actual value is a valid timestamp (within a 5-minute range)."""
        try:
            timestamp = int(actual_value)
            current_time = int(datetime.datetime.now().timestamp())
            return abs(current_time - timestamp) < 300  # 5-minute range
        except ValueError:
            return False

    def is_valid_mac_address(self, actual_value):
        """Check if the actual value is a valid MAC address."""
        mac_pattern = r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"
        return re.match(mac_pattern, actual_value) is not None
    ### Need to adds a define for vaild format rcode.
    def write_to_report(self, step_name, prefix, actual_value, result):
        """
        Write the result to the detailed report.
        """
        entry = f"{step_name}: Prefix={prefix}, Actual Value={actual_value}, Result={result}\n"
        with open(self.report_file, "a") as report:
            report.write(entry)
        self.results.append(entry)

    def validate_asynchrony(self, response):
        """Validate asynchronous responses by checking the response format."""
        if "[db_dump+ok]" in response:
            print("Asynchronous response valid.")
            logging.info("Asynchronous response valid.")
            return True
        print("Invalid asynchronous response.")
        logging.warning("Invalid asynchronous response.")
        return False

    def validate_restore(self, response, expected_status):
        """Validate that the restore process completed successfully."""
        if expected_status in response:
            print("Restore validation successful.")
            logging.info("Restore validation successful.")
            return True
        print("Restore validation failed.")
        logging.warning("Restore validation failed.")
        return False

    def validate_therapy_start(self, response, duration):
        """Simulate therapy start validation by waiting for the specified duration."""
        if "[therapy on+ok]" in response:
            print(f"Therapy start validated. Duration: {duration} seconds.")
            logging.info(f"Therapy start validated for {duration} seconds.")
            return True
        print("Therapy start validation failed.")
        logging.warning("Therapy start validation failed.")
        return False

    def validate_therapy_stop(self, response, expected_status):
        """Validate that the therapy stop process completed successfully."""
        if expected_status in response:
            print("Therapy stop validated successfully.")
            logging.info("Therapy stop validated successfully.")
            return True
        print("Therapy stop validation failed.")
        logging.warning("Therapy stop validation failed.")
        return False