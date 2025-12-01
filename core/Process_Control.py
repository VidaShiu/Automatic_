import datetime
import yaml
import threading
import logging
import time
from UART_communication import UARTCommunicator
from Conditional import Validator
from Statistic import ReportAggregator
from Serial_Port_Monitoring import monitor_serial_port

class TestRunner:
    def __init__(self, test_case_file, command_library_file, report_file):
        self.test_cases = self.load_yaml(test_case_file).get("test_cases", {})
        self.command_library = self.load_yaml(command_library_file).get("Command_Line", {})
        self.uart = UARTCommunicator()
        self.validator = Validator()
        self.user_inputs = self.load_user_inputs("Selected_Test_Plan.yml")
        self.report_writer = ReportAggregator(report_file)

    @staticmethod
    def load_yaml(file_path):
        try:
            with open(file_path, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            logging.error(f"YAML file not found: {file_path}")
            return {}
        except yaml.YAMLError as e:
            logging.error(f"Error parsing YAML file {file_path}: {e}")
            return {}

    @staticmethod
    def load_user_inputs(file_path):
        try:
            with open(file_path, "r") as file:
                data = yaml.safe_load(file)
                required_keys = ["selected_test_plan", "device_sn", "fw_version", "sw_version", "wifi_version"]
                if not all(key in data and data[key] for key in required_keys):
                    raise ValueError("Missing required keys or values in Selected_Test_Plan.yml")
                return data
        except (FileNotFoundError, ValueError, yaml.YAMLError) as e:
            logging.error(f"Error loading user inputs: {e}")
            return None

    @staticmethod
    def get_user_defined_condition(self, command_id):
        if command_id == "Get_SN_Number":
            return {"type": "equal", "expected": self.user_inputs.get("device_sn")}
        elif command_id == "Get_FW_Version":
            return {"type": "equal", "expected": self.user_inputs.get("fw_version")}
        elif command_id == "Get_LCM_Version":
            return {"type": "equal", "expected": self.user_inputs.get("sw_version")}
        elif command_id == "Get_WiFi_Version":
            return {"type": "equal", "expected": self.user_inputs.get("wifi_version")}
        return None

    def run_test_case(self, test_plan, stop_event):
        if test_plan not in self.test_cases:
            logging.error(f"No test cases defined for test plan: {test_plan}")
            print(f"No test cases defined for test plan: {test_plan}")
            return

        steps = self.test_cases.get(test_plan, [])
        if not steps:
            logging.error(f"No steps found for test plan: {test_plan}")
            print(f"No steps found for test plan: {test_plan}")
            return

        logging.info(f"Starting test plan: {test_plan}")
        print(f"Starting test plan: {test_plan}")

        start_time = time.time()
        for step in steps:
            for step_name, command_number in step.items():
                self.run_test_task(step_name, command_number, stop_event)

        end_time = time.time()
        duration = end_time - start_time
        logging.info(f"Test plan '{test_plan}' completed in {duration:.2f} seconds.")
        print(f"Test plan '{test_plan}' completed in {duration:.2f} seconds.")
        time.sleep(1)

    def run_test_task(self, step_name, command_number ,stop_event):
        if stop_event.is_set():
            print("Stop event detected, Stopping the test.")
            return

        command_entry = self.command_library.get(command_number)
        if not command_entry:
            logging.warning(f"Command {command_number} not found in Command_Line.yml")
            return

        command = command_entry["Command_Sends"]
        response_expectation = command_entry["Response_Expectation"]
        title = command_entry["Title"]
        condition_type = command_entry["Condition"]["type"]
        response = self.uart.send_command(command)

        logging.info(f"Executing {step_name}: {title}")
        print(f"Executing {step_name}: {title}")
        time.sleep(1)

        self.wait_for_response(condition_type)
        if not response:
            print(f"No response for {step_name}. Skipping...")
            return

         # Step 1: Classify the response
        prefix, actual_value = self.validator.classify_data(response)

        # Step 2: Validate prefix
        response_expectation = command_entry["Response_Expectation"]
        result = "Pass" if prefix == response_expectation else "Fail"
        self.validator.write_to_report(step_name, prefix, actual_value, result)

        if result == "Fail":
            return  # Skip further validation if prefix mismatches

        # Step 3: Validate actual_value if it exists
        if actual_value:
            condition = command_entry.get("Condition", {})
            is_valid = self.validator.validate_data(condition, actual_value)
            final_result = "Pass" if is_valid else "Fail"
            self.validator.write_to_report(step_name, prefix, actual_value, final_result)


def main():
    connection_event = threading.Event()
    stop_event = threading.Event() # fix:0109
    validator = Validator()  # Initialize the ResponseValidator
    aggregator = ReportAggregator(report_file)

    monitor_thread = threading.Thread(target=monitor_serial_port, args=(connection_event,stop_event)) # fix:0109
    monitor_thread.start()
    connection_event.wait()

    user_inputs = TestRunner.load_user_inputs("Selected_Test_Plan.yml")
    test_plan = user_inputs["selected_test_plan"]
    report_file = f"Test_Report_{datetime.datetime.now().strftime('%Y_%m_%d')}.txt"
    runner = TestRunner("Test_Case.yml", "Command_Line.yml", report_file)

    if not user_inputs:
        logging.error("No valid user inputs found.")
        return

    try:
        runner.run_test_case(test_plan, validator, aggregator, stop_event=stop_event)
    except Exception as e:
        logging.error(f"Error during test execution: {e}")
        print(f"Error: {e}")
    finally:
        connection_event.clear()
        stop_event.set()
        monitor_thread.join()
        logging.info("Serial monitoring stopped.")

    aggregator.write_summary_to_report()
    print(f"Test Completed: {test_plan}")
    logging.info(f"Test Completed: {test_plan}")


if __name__ == "__main__":
    main()
