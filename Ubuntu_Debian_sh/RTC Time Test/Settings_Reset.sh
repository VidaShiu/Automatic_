#!/bin/bash
echo "************************"
echo ""
echo "===== Settings Resets ====="
echo ""
echo "[Action]: Reset system time auto sync."
sudo systemctl start ntp.service

echo ""
echo "[Action]: Reset RTC time type to local."
sudo timedatectl set-local-rtc 1
