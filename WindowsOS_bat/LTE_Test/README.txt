## Purpose
1. Test Purpose: Verify the external connectivity quality and stability of the LTE module.
2. Test Environment: Windows OS
3. Script/Tool Name: LTE_ping.bat
## Configuration
4. Pre-condition:
   a. Open Command Prompt and execute the following command to retrieve the cellular interface name. (e.g.: Cellular 3)
   b. Open the batch file LTE_ping(TestVer).bat using Notepad or any text editor.
   c. Locate the placeholder cellular name (e.g., "Cellular 3") in the script and replace it.
   d. Save the changes by pressing Ctrl + S.
## Settings 
5. Open Task Scheduler and settings as follows:
   General:
   Name: LTE_Ping
   Run only user is looked on =Enable
   Run with highest privileges = Enable 
   Triggers>New:
   Begin the task: At log on
   Settings: One time
   Actions>New:
   Action: Start a program
   Settings>Browse: add Script
   Start in: Script’s directory location
## Usage
6. Test Methods:
   Step 1: Configure the power cycle test. The script will log each cycle automatically.
   Step 2: After the test is completed, retrieve the log file from the same directory.