@echo off
timeout /t 8 /nobreak >nul
setlocal enabledelayedexpansion

:: 計數器檔案
set COUNT_FILE=lte_ping_count.txt

:: 初始化或讀取執行次數
if not exist %COUNT_FILE% (
    echo 1 > %COUNT_FILE%
    set EXEC_COUNT=1
) else (
    set /p EXEC_COUNT=<%COUNT_FILE%
    set /a EXEC_COUNT+=1
    echo !EXEC_COUNT! > %COUNT_FILE%
)

:: 寫入執行次數與時間戳
echo === Loop Times: !EXEC_COUNT! === >> lte_ping.txt
echo %DATE% %TIME% >> lte_ping.txt

netsh mbn show interface >> lte_ping.txt
netsh mbn show radio interface="Cellular 3" >> lte_ping.txt

:: 抓取 LTE IP 並寫入
for /f "tokens=2 delims=:" %%A in ('netsh interface ipv4 show addresses ^| findstr /R "Cellular 3"') do (
    set LTE_IP=%%A
    set LTE_IP=!LTE_IP: =!
    echo !LTE_IP! >> lte_ping.txt
)

:: 執行 ping 並寫入
ping -n 1 8.8.8.8 >> lte_ping.txt
