import datetime
import yaml
import threading
import logging
import time
import re
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import serial

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"Test_Log_{datetime.datetime.now().strftime('%Y_%m_%d')}.log"),
        logging.StreamHandler()
    ]
)


# ====== Data Models ======
class TestState(Enum):
    """Test execution states"""
    IDLE = "idle"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


@dataclass
class TestResult:
    """Data class for individual test results"""
    step_name: str
    command_id: str
    title: str
    command_sent: str
    prefix: str
    actual_value: Optional[str]
    expected_value: Optional[Any]
    result: str  # "Pass" or "Fail"
    duration: float
    timestamp: datetime.datetime
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for reporting"""
        return {
            "step_name": self.step_name,
            "command_id": self.command_id,
            "title": self.title,
            "command": self.command_sent,
            "prefix": self.prefix,
            "actual_value": self.actual_value,
            "expected_value": self.expected_value,
            "result": self.result,
            "duration": f"{self.duration:.2f}s",
            "timestamp": self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            "error": self.error_message or "N/A"
        }


# ====== State Management ======

class TestStateManager:
    """Manages the state of test execution with comprehensive tracking"""
    
    def __init__(self):
        self.current_state = TestState.IDLE
        self.current_test_plan = None
        self.current_step = None
        self.test_results: List[TestResult] = []
        self.start_time = None
        self.end_time = None
        self._lock = threading.Lock()
        self._state_callbacks = []
        
        # Statistics tracking
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.skipped_tests = 0
    
    def register_state_callback(self, callback):
        """Register a callback for state changes"""
        self._state_callbacks.append(callback)
    
    def set_state(self, new_state: TestState):
        """Update test state with thread safety"""
        with self._lock:
            old_state = self.current_state
            self.current_state = new_state
            logging.info(f"State transition: {old_state.value} -> {new_state.value}")
            
            for callback in self._state_callbacks:
                try:
                    callback(old_state, new_state)
                except Exception as e:
                    logging.error(f"Callback error: {e}")
    
    def get_state(self) -> TestState:
        """Get current state thread-safely"""
        with self._lock:
            return self.current_state
    
    def start_test(self, test_plan: str):
        """Initialize test execution"""
        with self._lock:
            self.current_test_plan = test_plan
            self.start_time = time.time()
            self.test_results.clear()
            self.total_tests = 0
            self.passed_tests = 0
            self.failed_tests = 0
            self.skipped_tests = 0
            self.set_state(TestState.RUNNING)
    
    def complete_test(self):
        """Mark test as completed"""
        with self._lock:
            self.end_time = time.time()
            self.set_state(TestState.COMPLETED)
    
    def fail_test(self, error_message: str):
        """Mark test as failed"""
        with self._lock:
            self.end_time = time.time()
            self.set_state(TestState.FAILED)
            logging.error(f"Test failed: {error_message}")
    
    def add_result(self, result: TestResult):
        """Add a test result and update statistics"""
        with self._lock:
            self.test_results.append(result)
            self.total_tests += 1
            
            if result.result == "Pass":
                self.passed_tests += 1
            elif result.result == "Fail":
                self.failed_tests += 1
            else:
                self.skipped_tests += 1
    
    def get_duration(self) -> float:
        """Get test duration"""
        with self._lock:
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            elif self.start_time:
                return time.time() - self.start_time
            return 0.0
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive test statistics"""
        with self._lock:
            duration = self.get_duration()
            pass_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
            
            return {
                "test_plan": self.current_test_plan,
                "state": self.current_state.value,
                "total": self.total_tests,
                "passed": self.passed_tests,
                "failed": self.failed_tests,
                "skipped": self.skipped_tests,
                "pass_rate": pass_rate,
                "duration": duration,
                "start_time": datetime.datetime.fromtimestamp(self.start_time).strftime('%Y-%m-%d %H:%M:%S') if self.start_time else "N/A",
                "end_time": datetime.datetime.fromtimestamp(self.end_time).strftime('%Y-%m-%d %H:%M:%S') if self.end_time else "N/A"
            }
    
    def get_failed_tests(self) -> List[TestResult]:
        """Get list of failed tests"""
        with self._lock:
            return [r for r in self.test_results if r.result == "Fail"]
    
    def get_passed_tests(self) -> List[TestResult]:
        """Get list of passed tests"""
        with self._lock:
            return [r for r in self.test_results if r.result == "Pass"]


# ====== Validation & Judgment ======

class Validator:
    """Enhanced validator with all validation types"""
    
    def __init__(self):
        self.results = []
    
    def classify_data(self, response: str) -> tuple:
        """Split response into prefix and actual_value"""
        try:
            prefix, actual_value = response.split(" ", 1)
        except ValueError:
            prefix = response
            actual_value = None
        return prefix, actual_value
    
    def validate_data(self, condition: Dict, actual_value: str) -> bool:
        """Validate data based on condition type"""
        condition_type = condition.get("type")
        
        if condition_type == "equal":
            expected_value = condition.get("expected")
            return actual_value == expected_value
        
        elif condition_type == "between":
            low = int(condition.get("low", 0))
            high = int(condition.get("high", 0))
            try:
                return low <= int(actual_value) <= high
            except ValueError:
                return False
        
        elif condition_type == "valid timestamp":
            return self.is_valid_timestamp(actual_value)
        
        elif condition_type == "valid format_mac":
            return self.is_valid_mac_address(actual_value)
        
        elif condition_type == "valid format_rcode":
            return self.is_valid_rcode(actual_value)
        
        elif condition_type in ["asynchrony", "restore", "therapy start", "therapy stop"]:
            return True  # These are handled separately
        
        return False
    
    def is_valid_timestamp(self, actual_value: str) -> bool:
        """Check if timestamp is within 5-minute range"""
        try:
            timestamp = int(actual_value)
            current_time = int(datetime.datetime.now().timestamp())
            return abs(current_time - timestamp) < 300
        except ValueError:
            return False
    
    def is_valid_mac_address(self, actual_value: str) -> bool:
        """Check if MAC address format is valid"""
        mac_pattern = r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"
        return re.match(mac_pattern, actual_value) is not None
    
    def is_valid_rcode(self, actual_value: str) -> bool:
        """Validate Rendon code format"""
        # Add your specific rcode validation logic here
        # Example: check length, format, etc.
        return len(actual_value) > 0  # Placeholder


class TestJudge:
    """Handles test validation and judgment logic"""
    
    def __init__(self, validator: Validator, user_inputs: Dict[str, Any]):
        self.validator = validator
        self.user_inputs = user_inputs
    
    def get_expected_value(self, command_id: str) -> Optional[Any]:
        """Get expected value based on command ID"""
        mapping = {
            "Get_SN_Number": "device_sn",
            "Get_FW_Version": "fw_version",
            "Get_LCM_Version": "sw_version",
            "Get_WiFi_Version": "wifi_version"
        }
        
        key = mapping.get(command_id)
        return self.user_inputs.get(key) if key else None
    
    def judge_response(self,
                      step_name: str,
                      command_id: str,
                      title: str,
                      command_sent: str,
                      command_entry: Dict[str, Any],
                      response: str,
                      duration: float) -> TestResult:
        """Judge a test response and return TestResult"""
        
        result = TestResult(
            step_name=step_name,
            command_id=command_id,
            title=title,
            command_sent=command_sent,
            prefix="",
            actual_value="",
            expected_value=None,
            result="Fail",
            duration=duration,
            timestamp=datetime.datetime.now()
        )
        
        if not response:
            result.error_message = "No response received"
            return result
        
        # Step 1: Classify the response
        prefix, actual_value = self.validator.classify_data(response)
        result.prefix = prefix
        result.actual_value = actual_value
        
        # Step 2: Validate prefix
        response_expectation = command_entry.get("Response_Expectation", "")
        if prefix != response_expectation:
            result.result = "Fail"
            result.error_message = f"Prefix mismatch: expected '{response_expectation}', got '{prefix}'"
            return result
        
        # Step 3: Validate actual value if exists
        condition = command_entry.get("Condition", {})
        condition_type = condition.get("type")
        
        # Handle special condition types
        if condition_type in ["asynchrony", "restore", "therapy start", "therapy stop"]:
            result.result = "Pass"
            result.expected_value = condition.get("status", "N/A")
            return result
        
        # Validate actual value
        if actual_value:
            # Get expected value for user-defined conditions
            expected = self.get_expected_value(command_id)
            if expected:
                result.expected_value = expected
                condition["expected"] = expected
            
            is_valid = self.validator.validate_data(condition, actual_value)
            result.result = "Pass" if is_valid else "Fail"
            
            if not is_valid:
                result.error_message = f"Validation failed: expected '{expected}', got '{actual_value}'"
        else:
            result.result = "Pass"
        
        return result


# ====== Enhanced Statistics & Reporting ======

class EnhancedReportGenerator:
    """Generate comprehensive test reports with statistics"""
    
    def __init__(self, report_file: str, detail_file: str):
        self.report_file = report_file
        self.detail_file = detail_file
    
    def write_header(self, test_plan: str, user_inputs: Dict):
        """Write report header"""
        header = f"""
{'='*80}
                        TEST EXECUTION REPORT
{'='*80}
Test Plan:      {test_plan}
Generated:      {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Device SN:      {user_inputs.get('device_sn', 'N/A')}
FW Version:     {user_inputs.get('fw_version', 'N/A')}
SW Version:     {user_inputs.get('sw_version', 'N/A')}
WiFi Version:   {user_inputs.get('wifi_version', 'N/A')}
{'='*80}

"""
        with open(self.report_file, 'w') as f:
            f.write(header)
    
    def write_detailed_results(self, results: List[TestResult]):
        """Write detailed test results"""
        with open(self.detail_file, 'w') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"{'DETAILED TEST RESULTS':^80}\n")
            f.write(f"{'='*80}\n\n")
            
            for idx, result in enumerate(results, 1):
                f.write(f"Test #{idx}: {result.step_name}\n")
                f.write(f"  Title:         {result.title}\n")
                f.write(f"  Command:       {result.command_sent}\n")
                f.write(f"  Prefix:        {result.prefix}\n")
                f.write(f"  Actual Value:  {result.actual_value or 'N/A'}\n")
                f.write(f"  Expected:      {result.expected_value or 'N/A'}\n")
                f.write(f"  Result:        {result.result}\n")
                f.write(f"  Duration:      {result.duration:.2f}s\n")
                f.write(f"  Timestamp:     {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
                if result.error_message:
                    f.write(f"  Error:         {result.error_message}\n")
                f.write(f"{'-'*80}\n\n")
    
    def write_summary(self, stats: Dict, failed_tests: List[TestResult]):
        """Write comprehensive summary to report"""
        summary = f"""

{'='*80}
                        TEST EXECUTION SUMMARY
{'='*80}

Test Statistics:
  Total Tests:        {stats['total']}
  Passed:             {stats['passed']} ({stats['pass_rate']:.2f}%)
  Failed:             {stats['failed']}
  Skipped:            {stats['skipped']}

Execution Time:
  Start Time:         {stats['start_time']}
  End Time:           {stats['end_time']}
  Total Duration:     {stats['duration']:.2f} seconds ({stats['duration']/60:.2f} minutes)
  Average per Test:   {stats['duration']/stats['total']:.2f}s (if {stats['total']} > 0)

Final Status:         {stats['state'].upper()}

"""
        
        if failed_tests:
            summary += f"\n{'='*80}\n"
            summary += f"{'FAILED TESTS DETAILS':^80}\n"
            summary += f"{'='*80}\n\n"
            
            for idx, test in enumerate(failed_tests, 1):
                summary += f"{idx}. {test.step_name} - {test.title}\n"
                summary += f"   Error: {test.error_message}\n"
                summary += f"   Expected: {test.expected_value}, Got: {test.actual_value}\n\n"
        
        summary += f"\n{'='*80}\n"
        summary += f"Report saved to: {self.report_file}\n"
        summary += f"Details saved to: {self.detail_file}\n"
        summary += f"{'='*80}\n"
        
        with open(self.report_file, 'a') as f:
            f.write(summary)
        
        return summary
    
    def generate_statistics_table(self, results: List[TestResult]) -> str:
        """Generate statistics table"""
        table = f"\n{'='*80}\n"
        table += f"{'TEST RESULTS BY STEP':^80}\n"
        table += f"{'='*80}\n"
        table += f"{'Step':<15} {'Title':<35} {'Result':<10} {'Duration':<10}\n"
        table += f"{'-'*80}\n"
        
        for result in results:
            table += f"{result.step_name:<15} {result.title[:35]:<35} {result.result:<10} {result.duration:.2f}s\n"
        
        table += f"{'='*80}\n"
        
        with open(self.report_file, 'a') as f:
            f.write(table)
        
        return table


# ====== UART Communication ======

class UARTCommunicator:
    """Handles UART communication with proper response handling"""
    
    def __init__(self, port="/dev/ttyUSB0", baudrate=115200, timeout=2):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
    
    def send_command(self, command: str) -> Optional[str]:
        """Send command and receive response"""
        try:
            with serial.Serial(port=self.port, baudrate=self.baudrate, timeout=self.timeout) as ser:
                # Send command
                ser.write(f"{command}\n".encode('utf-8'))
                logging.info(f"Sent command: {command}")
                
                # Wait for response
                time.sleep(0.5)
                
                # Read response
                if ser.in_waiting > 0:
                    response = ser.readline().decode('utf-8').strip()
                    logging.info(f"Received response: {response}")
                    return response
                else:
                    logging.warning(f"No response for command: {command}")
                    return None
                    
        except serial.SerialException as e:
            logging.error(f"UART Error: {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return None


# ====== Test Runner ======

class TestRunner:
    """Orchestrates test execution with separated concerns"""
    
    def __init__(self, test_case_file: str, command_library_file: str, 
                 report_file: str, detail_file: str):
        self.test_cases = self.load_yaml(test_case_file).get("test_cases", {})
        self.command_library = self.load_yaml(command_library_file).get("Command_Line", {})
        self.uart = UARTCommunicator()
        self.validator = Validator()
        self.user_inputs = self.load_user_inputs("Selected_Test_Plan.yml")
        
        # Initialize separated components
        self.state_manager = TestStateManager()
        self.judge = TestJudge(self.validator, self.user_inputs)
        self.report_generator = EnhancedReportGenerator(report_file, detail_file)
        
        # Register callbacks
        self.state_manager.register_state_callback(self._on_state_change)
    
    @staticmethod
    def load_yaml(file_path: str) -> Dict:
        """Load YAML file"""
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
    def load_user_inputs(file_path: str) -> Optional[Dict]:
        """Load user inputs from YAML"""
        try:
            with open(file_path, "r") as file:
                data = yaml.safe_load(file)
                required_keys = ["selected_test_plan", "device_sn", "fw_version",
                               "sw_version", "wifi_version"]
                if not all(key in data and data[key] for key in required_keys):
                    raise ValueError("Missing required keys in Selected_Test_Plan.yml")
                return data
        except (FileNotFoundError, ValueError, yaml.YAMLError) as e:
            logging.error(f"Error loading user inputs: {e}")
            return None
    
    def _on_state_change(self, old_state: TestState, new_state: TestState):
        """Callback for state changes"""
        print(f"[STATE] {old_state.value} -> {new_state.value}")
    
    def wait_for_response(self, condition_type: str):
        """Wait based on condition type"""
        wait_times = {
            "equal": 1.0,
            "valid timestamp": 0.5,
            "valid format_mac": 0.5,
            "valid format_rcode": 0.5,
            "asynchrony": 2.0,
            "restore": 10.0,
            "therapy start": 1.0,
            "therapy stop": 5.0
        }
        time.sleep(wait_times.get(condition_type, 1.0))
    
    def run_test_case(self, test_plan: str, stop_event: threading.Event):
        """Execute test plan"""
        
        if test_plan not in self.test_cases:
            self.state_manager.fail_test(f"No test cases defined for: {test_plan}")
            return
        
        steps = self.test_cases.get(test_plan, [])
        if not steps:
            self.state_manager.fail_test(f"No steps found for: {test_plan}")
            return
        
        # Write report header
        self.report_generator.write_header(test_plan, self.user_inputs)
        
        # Start test
        self.state_manager.start_test(test_plan)
        print(f"\n{'='*80}")
        print(f"Starting Test Plan: {test_plan}")
        print(f"{'='*80}\n")
        
        try:
            # Execute steps
            for step in steps:
                if stop_event.is_set():
                    self.state_manager.set_state(TestState.STOPPED)
                    print("\n[STOP] Test execution stopped by user")
                    break
                
                for step_name, command_number in step.items():
                    if command_number is None:
                        continue
                    
                    result = self.run_test_task(step_name, str(command_number), stop_event)
                    if result:
                        self.state_manager.add_result(result)
                        
                        # Print progress
                        status_icon = "✓" if result.result == "Pass" else "✗"
                        print(f"  {status_icon} {result.step_name}: {result.result} ({result.duration:.2f}s)")
            
            # Complete test
            if not stop_event.is_set():
                self.state_manager.complete_test()
            
        except Exception as e:
            self.state_manager.fail_test(str(e))
            logging.error(f"Error during test execution: {e}")
            raise
        
        # Generate reports
        self.generate_final_reports()
    
    def run_test_task(self, step_name: str, command_number: str,
                     stop_event: threading.Event) -> Optional[TestResult]:
        """Execute a single test task"""
        
        if stop_event.is_set():
            return None
        
        command_entry = self.command_library.get(int(command_number))
        if not command_entry:
            logging.warning(f"Command {command_number} not found")
            return None
        
        command = command_entry["Command_Sends"]
        title = command_entry["Title"]
        command_id = command_entry["ID"]
        condition = command_entry.get("Condition", {})
        condition_type = condition.get("type", "equal")
        
        # Execute test
        start_time = time.time()
        response = self.uart.send_command(command)
        self.wait_for_response(condition_type)
        duration = time.time() - start_time
        
        # Judge result
        result = self.judge.judge_response(
            step_name=step_name,
            command_id=command_id,
            title=title,
            command_sent=command,
            command_entry=command_entry,
            response=response,
            duration=duration
        )
        
        return result
    
    def generate_final_reports(self):
        """Generate final reports and statistics"""
        stats = self.state_manager.get_statistics()
        failed_tests = self.state_manager.get_failed_tests()
        
        # Write detailed results
        self.report_generator.write_detailed_results(self.state_manager.test_results)
        
        # Write statistics table
        self.report_generator.generate_statistics_table(self.state_manager.test_results)
        
        # Write summary
        summary = self.report_generator.write_summary(stats, failed_tests)
        
        # Print to console
        print(summary)


# ======Main Entry Point ======

def main():
    """Main entry point"""
    from Serial_Port_Monitoring import monitor_serial_port
    
    connection_event = threading.Event()
    stop_event = threading.Event()
    
    print("Initializing serial port monitoring...")
    
    # Start serial port monitoring
    monitor_thread = threading.Thread(
        target=monitor_serial_port,
        args=(connection_event, stop_event),
        daemon=True
    )
    monitor_thread.start()
    
    # Wait for connection
    print("Waiting for UART connection...")
    if not connection_event.wait(timeout=30):
        print("Failed to establish UART connection within timeout")
        stop_event.set()
        return
    
    print("UART connection established!\n")
    
    # Load configuration
    user_inputs = TestRunner.load_user_inputs("Selected_Test_Plan.yml")
    if not user_inputs:
        logging.error("No valid user inputs found")
        return
    
    test_plan = user_inputs["selected_test_plan"]
    timestamp = datetime.datetime.now().strftime('%Y_%m_%d_%H%M%S')
    report_file = f"Test_Report_{timestamp}.txt"
    detail_file = f"Test_Details_{timestamp}.txt"
    
    # Initialize test runner
    runner = TestRunner("Test_Case.yml", "Command_Line.yml", report_file, detail_file)
    
    try:
        # Run test
        runner.run_test_case(test_plan, stop_event)
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        stop_event.set()
        
    except Exception as e:
        logging.error(f"Error during test execution: {e}")
        print(f"Error: {e}")
        
    finally:
        # Cleanup
        connection_event.clear()
        stop_event.set()
        monitor_thread.join(timeout=5)
        logging.info("Test execution completed")
    
    print(f"\n{'='*80}")
    print(f"Test execution finished!")
    print(f"Reports saved to:")
    print(f"  - {report_file}")
    print(f"  - {detail_file}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()