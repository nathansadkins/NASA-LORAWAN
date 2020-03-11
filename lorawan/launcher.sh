#!/bin/sh
# launcher.sh
# navigate to home directory, then to this directory, execute, go back home

cd /
cd home/pi/lorawan
sudo python3.7 lorawan.py
cd /
