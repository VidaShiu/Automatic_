import os
import logging
from datetime import datetime


class ReportAggregator:
    """Generates and updates the test report."""

    def __init__(self, report_file):
        self.report_file = report_file
        self.test_result = []

    def add_test_result(self, step_name, result, duration):
        """Store individual test result for later aggregation."""
        self.test_results.append({
            "step_name": step_name,
            "result": result,
            "duration": duration
        })

    def summarize_results(self):
        """Summarize test results into counts and time duration."""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["result"] == "Pass")
        failed_tests = total_tests - passed_tests
        total_duration = sum(result["duration"] for result in self.test_results)

        summary = {
            "Total Tests": total_tests,
            "Passed": passed_tests,
            "Failed": failed_tests,
            "Total Duration (s)": round(total_duration, 2)
        }
        return summary

    def write_summary_to_report(self):
        """Write the aggregated summary to the report file."""
        summary = self.summarize_results()
        with open(self.report_file, "a") as file:
            file.write("\nSummary of Test Results:\n")
            for key, value in summary.items():
                file.write(f"{key}: {value}\n")
        logging.info("Summary written to report.")

