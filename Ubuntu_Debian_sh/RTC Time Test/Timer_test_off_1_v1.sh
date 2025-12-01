#!/bin/bash

timestamp=$(date +"%Y-%m-%d-%H-%M-%S") #建立時間戳記(格式：YYYY-MM-DD-HH-MM-SS)
logfile="RTC_Off_Test_$timestamp.txt" #使用時間戳記命名log

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

echo ""
echo "===== Start The Test =====" | tee -a "$logfile"

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

for i in $(seq 60 -5 0); do
  echo "Shutdown in $i seconds..."
  sleep 5
done
sudo shutdown -h now

