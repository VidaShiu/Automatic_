## Purpose
1. Test Purpose: Verify the difference between RTC, system time, and NTP time.
2. Test Environment: Ubuntu & Debian OS
3. Script/Tool Name: Timer_test_on.sh/Timer_test_off_1.sh/Timer_test_off_2.sh
## Configuration
4. Pre-condition:
   a. Connected with Ethernet first.
   b. Execute the terminal and insert the command "sudo bash ./install.sh" to install the support service.
## Settings 
   a. Select mode 1 or 2 to choose condition "duration" or "loop cycle"
   b. Further input of expiration time or recurrence time according to mode selection.
## Usage
5. Test methods:
   a. Execute the terminal and insert the command "sudo bash ./Timer_test_on.sh"
   b. After the RTC on test finishes, execute the terminal and insert the command "sudo bash ./Timer_test_off_1.sh"
   c. Waiting for 24 hrs.
   d. After the RTC on test finishes, execute the terminal and insert the command "sudo bash ./Timer_test_off_2.sh"
## Structure

RTC Time Test/
┣ Install.sh -> Install necessary services
┣ Timer_test_on.sh -> RTC On Test
┣ Timer_test_off_1.sh -> RTC Off Test: Init, Records Start Time, Shutdown
┣ Timer_test_off_2.sh -> RTC Off Test: Records End Time, time difference calculation
┣ RTC_On_Test_$timestamp.txt/Time_Compare_$timestamp.txt ->log for RTC On Test
┗ RTC_Off_Test_$timestamp.txt/Time_Compare_Off_$timestamp.txt ->log for RTC Off Test