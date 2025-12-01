#!/bin/bash

echo"===== Installing... ====="
sudo apt install linux-firmware
wait
sudo apt update
wait
sudo apt install util-linux
wait
sudo apt install util-linux-extra
wait
sudo hwclock --version
wait
echo"===== Install Complete ====="


