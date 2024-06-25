#!/bin/sh
home_dir=$HOME
cd "$HOME/LMCMScripts/lmc/"
nice -n -10 python3 lmcsupervisor.py
