#!/bin/bash
echo "************************"
# 使用者有5秒輸入測試時間(sec.)，否則預設為86400秒(24小時)
echo "Please Enter The Test Time (in seconds) And Press Enter To Confirm."
read -t 5 -p "5 Seconds Buffer Time, Enter Or Wait (Set Default Value): " inputchar
echo $inputchar > inputchar.txt
a=$(cat inputchar.txt)
dest=
if [ "$a" = "$dest" ]; then
  echo "Set The Test Time Duration: 24 hrs"
  echo
  a=86400
else 
  echo "Saved And Excute That Settings"
  wait
fi 
echo ""
echo "===== Time Is Initializing... ====="
echo "[Action]: Set the hardware clock (RTC) to use UTC time."
sudo timedatectl set-local-rtc 0 # RTC設定為UTC
echo "[Action]: Manually sychronize system time with NTP time."
sudo ntpdate time.stdtime.gov.tw
echo "[Action]: Manually writting system time to RTC."
sudo hwclock --systohc
echo "[Action]: Automatic synchronization is disable."
sudo systemctl stop ntp.service

wait

timestamp=$(date +"%Y-%m-%d-%H-%M-%S") # Creates timestamp(format: YYYY-MM-DD-HH-MM-SS)
logfile="RTC_On_Test_$timestamp.txt" # Named log file
comparefile="Time_Compare_$timestamp.txt" # Name compare file

echo ""
echo "===== Start The Test =====" | tee -a "$logfile"

(
  echo "[NTP Offset] $(sudo ntpdate -q time.stdtime.gov.tw | tee -a "$logfile")" # Get current NTP time
) &

(
  echo "[RTC] $(sudo hwclock --show | tee -a "$logfile")" # Get current RTC time
) &

(
  echo "[System] $(sudo date +"%Y-%m-%d %H:%M:%S.%6N" | tee -a "$logfile")" #Get current system time
) &

wait

sleep $a

echo " ===== End Time Recording... =====" | tee -a "$logfile"

(
  echo "[NTP Offset] $(sudo ntpdate -q time.stdtime.gov.tw | tee -a "$logfile")" # Get current system time
) &

(
  echo "[RTC] $(sudo hwclock --show | tee -a "$logfile")" # Get current RTC time
) &

(
  echo "[System] $(sudo date +"%Y-%m-%d %H:%M:%S.%6N" | tee -a "$logfile")" #Get current NTP time
) &

wait
echo ""
echo "===== Time Comparison... ====="
touch "$comparefile"

# System time (最後一筆排除 +08:00)
system_raw=$(grep -v '\+08:00' "$logfile" | grep -Eo '^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}' | tail -n 1)
system_epoch=$(date -d "$system_raw" +%s.%6N)

# RTC time (最後一筆含 +08:00)
rtc_raw=$(grep '\+08:00' "$logfile" | grep -Eo '^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}\+08:00' | tail -n 1)
rtc_epoch=$(date -d "$rtc_raw" +%s.%6N)

# NTP offset (最後一筆含正負號)
offset_line=$(grep "offset" "$logfile" | tail -n 1)
offset_value=$(echo "$offset_line" | grep -oP 'offset\s+[+-]?[0-9]+\.[0-9]+')
# 推估 NTP Time（NTP = System - offset）
ntp_epoch=$(echo "$system_epoch - $offset_value" | bc)
# 計算差距（浮點秒）
diff_sys_ntp=$(echo "$system_epoch - $ntp_epoch" | bc)
diff_rtc_ntp=$(echo "$rtc_epoch - $ntp_epoch" | bc)

# Output the result
{
echo "===== Comparison Result ====="
echo "System Time: $system_raw"
echo "RTC Time   : $rtc_raw"
echo "NTP Time   : $offset_line"
echo ""
echo "System Time vs NTP Time Difference: ${diff_sys_ntp} seconds"
echo "RTC Time vs NTP Time Difference: ${diff_rtc_ntp} seconds"
} | tee -a "$comparefile"

wait
echo ""
echo "===== Test Completed ====="
wait
echo ""
echo "===== Calling Settings Setup... ====="
sudo bash ./Settings_Reset.sh

# echo "===== Calling Next Test... ====="
# sudo bash ./Timer_test_off_1_1003.sh
