#!/bin/bash
timestamp=$(date +"%Y-%m-%d-%H-%M-%S") #建立時間戳記(格式：YYYY-MM-DD-HH-MM-SS)
logfile="RTC_Off_Test_$timestamp.txt" #使用時間戳記命名log
comparefile="Time_Compare_Off_$timestamp.txt" # Name compare file

echo " =====Test Has Been Completed =====" | tee -a "$logfile"

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
# diff_sys_ntp=$(echo "$system_epoch - $ntp_epoch" | bc)
diff_rtc_ntp=$(echo "$rtc_epoch - $ntp_epoch" | bc)

# Output the result
{
echo "===== Comparison Result ====="
echo "System Time: $system_raw"
echo "RTC Time   : $rtc_raw"
echo "NTP Time   : $offset_line"
echo ""
# echo "System Time vs NTP Time Difference: ${diff_sys_ntp} seconds"
echo "RTC Time vs NTP Time Difference: ${diff_rtc_ntp} seconds"
} | tee -a "$comparefile"

wait
echo ""
echo "===== Test Completed ====="
wait
echo ""
echo "===== Calling Settings Setup... ====="
sudo bash ./Settings_Reset.sh
