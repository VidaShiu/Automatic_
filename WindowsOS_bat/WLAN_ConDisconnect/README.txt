## Purpose
1. Test Purpose: Verify the external connectivity quality and stability of the WLAN module on the service phase.
2. Test Environment: Windows OS
3. Script/Tool Name: WLAN_connect_disconnect_test.bat
## Configuration
4. Pre-condition:
   a. Connect with the Wi-Fi.
## Settings 
5. Edit test script with note or notepad++, and set the configuration as follows.
   a. PROFILE is SSID. e.g., Advantecher.
   b. TARGET_IP is ping IP address.
   c. MAX_RUNS is test times.
## Usage
6. Test Methods:
   Step 1: Save the script edition and double-click to execute automatically.
## Structure

WLAN_ConDisconnect/
┣ WLAN_connect_disconnect_test.bat
  ┗ wifi_toggle.txt -> log for test result