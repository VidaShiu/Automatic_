#! /bin/bash
echo "************************"

echo "===== Set the Test Duration Or Loop Times ====="
echo ""
echo "Select test mode:"
echo "1) Duration Mode (Run for N Seconds)"
echo "2) Loop Mode (Run N times)"
read -p "Enter 1 or 2: " mode

if [ "$mode" == "1" ]; then
   read -t 10 -p "10 Seconds Buffer Time, Enter Or Wait (Set Default Value): " duetime
   duetime=${duetime:-86400}
   echo "Set the test duration: $duetime seconds."
elif
   [ "$mode" == "2" ]; then
   read -t 10 -p "10 Seconds Buffer Time, Enter Or Wait (Set Default Value): " looptimes
   looptimes=${looptimes:-10}
   echo "Set the loop time is: $looptimes times."

else
   echo "[Error Message] Invalid or input timeout, exit. "
   exit 1
fi 

ping_server=${1:-8.8.8.8}
ping_count=${2:-10}

timestamp=$(date +"%Y%m%d_%H%M")
sudo mkdir -p ./test_result/
logfile="./test_result/Network_Test_$timestamp.txt"


echo ""
echo "===== Start The Test ====="
echo "[Info] Network test started at $(date)" | tee -a $logfile
echo "[Action] Ping target: $ping_server, Count: $ping_count" | tee -a $logfile

#test process: mode 1
start_time=$(date +%s)

if [ "$mode" == "1" ]; then
   echo "[Info] Duration mode for $duetime seconds" | tee -a $logfile
   while true; do
         current_time=$(date +%s)
         elapsed=$(( current_time - start_time))
         if [ "$elapsed" -ge "$duetime" ];then
            echo "[Info] Time limit ($duetime sec), Stop test."  | tee -a $logfile
            break

         fi
         echo ""
         echo "===== Running test at $(date) (elapsed: ${elapsed}s) ====="
         ping_result=$(ping -c "$ping_count" "$ping_server")
         ping_loss=$(echo "$ping_result" | grep "packet loss" | awk -F',' '{print $3}' | awk '{print $1}')
         avg_time=$(echo "$ping_result" |grep "rtt" | awk -F'/' '{print $5}')
         echo "[Result] Packet loss: $ping_loss" | tee -a $logfile
         echo "[Result] Avg latency: ${avg_time}ms" | tee -a $logfile
         sleep 3
    done

elif [ "$mode" == "2" ]; then
     echo "[Info] Loop mode for $looptimes times" | tee -a $logfile
     for (( i=1; i<=looptimes; i++ )); do
          echo ""
          echo "===== Running test #$i at $(date) ====="
          ping_result=$(ping -c "$ping_count" "$ping_server")
          ping_loss=$(echo "$ping_result" | grep "packet loss" | awk '{print $6}')
          avg_time=$(echo "$ping_result" |grep "rtt" | awk -F'/' '{print $5}')
          echo "[Result] Packet loss: $ping_loss" | tee -a $logfile
          echo "[Result] Avg latency: ${avg_time}ms" | tee -a $logfile
         sleep 3
    done
fi


if command -v iperf3 > /dev/null 2 >&1; then
    echo "[Info] Running iperf3 thoughput test..." | tee -a $logfile
    iperf3 -c "$ping_server" -t 10 >> "$logfile" 2>&1
else
    echo "[Warn] iperf3 not found, skip throughput test."  | tee -a $logfile
fi

echo ""
echo "===== End The Test ====="
echo "[Info] Network Test Has Been Completed at $(date)" | tee -a $logfile