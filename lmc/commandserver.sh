#!/bin/sh
home_dir=$HOME/LMCMScripts
cd "$HOME/LMCMScripts/lmc/"
python3 lmcinitializer.py && nice -n -10 python3 commandserver.py
