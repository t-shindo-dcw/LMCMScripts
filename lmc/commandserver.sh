#!/bin/sh
home_dir=$HOME
cd "$HOME/lmc/"
python3 lmcinitializer.py && nice -n -10 python3 commandserver.py
