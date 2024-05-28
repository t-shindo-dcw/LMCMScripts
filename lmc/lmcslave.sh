#!/bin/sh
home_dir=$HOME
cd "$HOME/lmc/"
sudo -E nice -n -10 "$HOME/lmc/LEDMultiControl/LEDMultiControl" -s "-p$HOME/lmc/pattern/LMC_FC_128x192.dat"
