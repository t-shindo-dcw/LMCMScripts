#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os.path
import lmc_common
import subprocess
import re
#import pdb; pdb.set_trace()

###############################################################################
#  automatic WiFi mode selector script
#
# (C) D Craftwork 2023.8
###############################################################################


def WifiUpdate(lmcsc):
    global logger

  
    print ("-----------------------");
    print (" Add WiFi access point")
    print ("-----------------------");

    # Start Wifi
    #Configから、Wifiの情報を作る。

    #Command = "sudo mv /etc/hostapd/hostapd.conf hostapd.bak"
    ExecutionCommand=['sudo','cp','/etc/hostapd/hostapd.conf','hostapd.bak']
    print (" ".join(ExecutionCommand))
    subprocess.Popen(ExecutionCommand, shell=False)


    Modify_hostapd_conf(lmcsc)

    #Command = "sudo mv hostapd.conf /etc/hostapd/"
    ExecutionCommand=['sudo','cp','hostapd.conf','/etc/hostapd/']
    print (" ".join(ExecutionCommand))
    subprocess.Popen(ExecutionCommand, shell=False)


def Modify_hostapd_conf(lmcsc):

     print ("Modify hostapd.conf from wifi access point information")

#
#    string="ssid="+lmcsc.AP_SSID
#    string="wpa_passphrase="+lmcsc.AP_KEY

     file_name = "/etc/hostapd/hostapd.conf"
     new_password = lmcsc.AP_KEY
     new_ssid=lmcsc.AP_SSID

     # ファイルを読み込む
     with open(file_name, mode='r') as file:
        content = file.read()

     # 正規表現でssidとwpa_passphraseを検索して置換
     file_content = re.sub(r'^ssid=.+', f'ssid={new_ssid}', content, flags=re.MULTILINE)
     new_content = re.sub(r'^wpa_passphrase=.+', f'wpa_passphrase={new_password}', file_content, flags=re.MULTILINE)

     #print("--------")
     #print(new_content)
     #print("--------")

     # 変更後の内容をファイルに書き込む
     file_name2 = "hostapd.conf"
     with open(file_name2, mode='w') as file2:
         file2.write(new_content)

     print("Modified file hostapd.conf ")

