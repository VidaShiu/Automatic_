## Purpose
1. Test Purpose: The embedded system communicates with the DUT via UART and sends hardware commands to perform behavior control tests.
2. Test Environment: Windows & Ubuntu & Debian OS
## Configuration
4. Pre-condition:
   a. Connected the DUT with the UART dongle(and GPIO).
   b. Execute the terminal on Windows or Ubuntu, or Debian.
## Settings 
   a. Select test type.
   b. Insert the serial number.
## Structure

Function Test/
┣ ctrl
  ┣ Serial_Port_Monitoring.py
  ┗ UART_communication.py
┣ core
  ┣ Process_Control.py
  ┣ Conditional
  ┗ Statistic.py
┣ gui
  ┗ GUI.py
┣ library
  ┣ Test_Plan_List.yml
  ┣ Command_Line.yml
  ┗ Test_Case.yml