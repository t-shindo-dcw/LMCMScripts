#!/bin/sh

sudo modprobe rtc-ds3232
echo ds3231 0x68 | sudo tee /sys/class/i2c-adapter/i2c-1/new_device
sudo hwclock -s
