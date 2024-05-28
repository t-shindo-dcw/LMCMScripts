#!/bin/sh
home_dir=$HOME
cd "$HOME/lmc/"
nice -n -10 python3 lmcsupervisor.py
