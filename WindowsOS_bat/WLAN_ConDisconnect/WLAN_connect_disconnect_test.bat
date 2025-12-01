@echo off
setlocal enabledelayedexpansion

:: ========= 可自訂參數 =========
set COUNT_FILE=wlan_ping_count.txt
set LOG_FILE=wifi_toggle.log
set INTERFACE=Wi-Fi
set PROFILE=Advantecher
set TARGET_IP=8.8.8.8
set MAX_RUNS=1000
set INTERVAL=10
set BUFFER_TIME=20
:: ==============================

:: 設語言為 EN（避免亂碼）
chcp 437 >nul

:: 初始化或讀取執行次數
if not exist %COUNT_FILE% (
    echo 0 > %COUNT_FILE%
)
set /p EXEC_COUNT=<%COUNT_FILE%

:: 主循環開始
:LOOP
if !EXEC_COUNT! geq %MAX_RUNS% (
    echo Test Conplete, total %MAX_RUNS% Times
    echo Finished at %DATE% %TIME% >> %LOG_FILE%
    echo ===== Wi-Fi toggle end ===== >> %LOG_FILE%
    goto :EOF
)

set /a EXEC_COUNT+=1
echo !EXEC_COUNT! > %COUNT_FILE%

:: 記錄執行資訊
echo === Loop Times: !EXEC_COUNT! === >> %LOG_FILE%
echo %DATE% %TIME% >> %LOG_FILE%

:: 斷線
echo Disconnecting... >> %LOG_FILE%
netsh wlan disconnect interface="%INTERFACE%" >> %LOG_FILE% 2>&1
timeout /t 3 /nobreak >nul

:: 連線
echo Connecting to profile %PROFILE%... >> %LOG_FILE%
netsh wlan connect name="%PROFILE%" interface="%INTERFACE%" >> %LOG_FILE% 2>&1

:: 取連線資訊
timeout /t 6 /nobreak >nul
netsh wlan show interfaces | find "Description" >> %LOG_FILE%
netsh wlan show interfaces | find "SSID" >> %LOG_FILE%
netsh wlan show interfaces | find "State" >> %LOG_FILE%
netsh wlan show interfaces | find "Rssi" >> %LOG_FILE%

:: 執行 ping 並寫入
ping -n 10 %TARGET_IP% >> %LOG_FILE%

:: 等待主要間隔 + 緩衝時間
set /a WAIT_TIME=%INTERVAL%+%BUFFER_TIME%
echo Waiting for !WAIT_TIME! seconds (interval + buffer)... >> %LOG_FILE%
timeout /t !WAIT_TIME! /nobreak >nul

goto LOOP
