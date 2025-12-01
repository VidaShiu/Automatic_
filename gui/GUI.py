import tkinter as tk
from tkinter import ttk, messagebox
import yaml
import subprocess
import os
import datetime


class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GFM50-Ventilator Automatic Test Process")
        self.root.geometry("550x550")

        self.output_dir = '.'
        self.output_file = self.generate_filename()

        # Initialize input variables
        self.dvsn_data = ""
        self.fwv_data = ""
        self.swv_data = ""
        self.wifiv_data = ""
        self.testcycle_data = ""

        # Load test plans from YAML
        self.test_plan_data = self.load_yaml('Test_Plan_List.yml', 'test_plans')

        # Set up GUI components
        self.setup_gui()

    def setup_gui(self):
        """Set up the GUI components."""
        tk.Label(self.root, text="Select A Test Plan:").grid(row=0, column=0, pady=5)
        self.test_plan_var = tk.StringVar()
        ttk.Combobox(self.root, textvariable=self.test_plan_var, values=self.test_plan_data).grid(row=0, column=1, pady=5)

        self.add_input_field("Device SN:", 1, self.dvsn_data, "dvsn_var")
        self.add_input_field("Firmware Version:", 2, self.fwv_data, "fwv_var")
        self.add_input_field("Software Version:", 3, self.swv_data, "swv_var")
        self.add_input_field("Wi-Fi Version:", 4, self.wifiv_data, "wifiv_var")
        self.add_input_field("Test Cycle:", 5, self.testcycle_data, "testcycle_var")

        tk.Button(self.root, text="Next", command=self.trigger_Process_Control).grid(row=10, column=0, pady=20)

    def add_input_field(self, label, row, default_value, var_name):
        """Add a labeled input field."""
        tk.Label(self.root, text=label).grid(row=row, column=0, pady=5)
        setattr(self, var_name, tk.StringVar(value=default_value))
        tk.Entry(self.root, textvariable=getattr(self, var_name)).grid(row=row, column=1, pady=5)

    def load_yaml(self, file_path, key):
        """Load a list of test plans from YAML."""
        if not os.path.exists(file_path):
            print(f"Error: File {file_path} does not exist.")
            return []
        try:
            with open(file_path, 'r') as file:
                data = yaml.safe_load(file)
                return data.get(key, [])
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return []

    def save_test_plan(self, test_plan):
        saved_file = "Selected_Test_Plan.yml"
        try:
        # Use a regular dictionary to avoid OrderedDict serialization issues
            data = {
               "selected_test_plan": test_plan,
               "device_sn": self.dvsn_var.get(),
               "fw_version": self.fwv_var.get(),
               "sw_version": self.swv_var.get(),
               "wifi_version": self.wifiv_var.get()
            }
            with open(saved_file, 'w') as file:
             yaml.dump(data, file, default_flow_style=False)
            print(f"Test plan and user inputs saved to {saved_file}")
        except Exception as e:
            print(f"Error saving test plan: {e}")

    def generate_filename(self):
        """Generate a filename based on the current date."""
        current_date = datetime.datetime.now().strftime("%Y_%m_%d")
        return os.path.join(self.output_dir, f"Test_Report_{current_date}.txt")

    def ensure_file_exists(self):
        """Ensure the test report file exists."""
        if not os.path.exists(self.output_file):
            try:
                with open(self.output_file, 'w') as file:
                    file.write("Test Report\n")
                print(f"File created: {self.output_file}")
            except Exception as e:
                print(f"Error creating report file: {e}")
                messagebox.showerror("File Error", f"Could not create report file: {e}")

    def validate_inputs(self):
        """Validate user inputs."""
        if len(self.dvsn_var.get()) != 13:
            messagebox.showerror("Validation Error", "Device SN must be exactly 13 characters long.")
            return False
        return True

    def trigger_Process_Control(self):
        """Save inputs and trigger Process_Control.py."""
        if not self.validate_inputs():
            return

        selected_test_plan = self.test_plan_var.get()
        if not selected_test_plan or selected_test_plan == "Choose a Test Plan":
            messagebox.showerror("Validation Error", "Please select a valid Test Plan.")
            return

        self.save_test_plan(selected_test_plan)

        # Write test environment details
        self.ensure_file_exists()
        try:
            with open(self.output_file, 'a') as file:
                file.write("Test Environment:\n")
                file.write(f"  Device SN: {self.dvsn_var.get()}\n")
                file.write(f"  FW Version: {self.fwv_var.get()}\n")
                file.write(f"  SW Version: {self.swv_var.get()}\n")
                file.write(f"  Wi-Fi Version: {self.wifiv_var.get()}\n")
                file.write("\n")
                file.write("=====================\n")
                file.write(f"Part.I-Summary\n")
                file.write(f"  Test Type: {selected_test_plan}\n")
                file.write(f"  Test Cycle: {self.testcycle_var.get()}\n")
            print(f"Data written to {self.output_file}")
        except Exception as e:
            print(f"Error writing to report file: {e}")
            messagebox.showerror("File Error", f"Could not write to report file: {e}")

        # Trigger Process_Control.py
        try:
            subprocess.run(["python", "Process_Control.py"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Execution Error: {e}")
            messagebox.showerror("Execution Error", f"Process_Control.py failed: {e}")
        except FileNotFoundError:
            print("Process_Control.py not found.")
            messagebox.showerror("File Not Found", "Process_Control.py not found.")


if __name__ == '__main__':
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()
