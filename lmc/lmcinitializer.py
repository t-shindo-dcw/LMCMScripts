#!/usr/bin/env python3
# -*- coding: utf-8 -*-

###############################################################################
# LMC-01 LMC Updator Linux-Python
# LMCInitializer.py : 
# Ver.0.1 2018/11/13
#
# (C) Kyowa System Co.,ltd.   K Shindo
###############################################################################

import sys
import os.path
import shutil
import json
import struct
import filecmp
import logging
import logging.handlers
import subprocess
import time 

import drawmessage
import lmc_common
import wifimanager

absscriptdir = os.path.abspath(os.path.dirname(__file__))    #絶対ディレクトリの取得　lmcフォルダになる

DEBUGMODE = True        #False

LOGFILENAME = "lmcs_command.log"

logger = None


lmcsc = lmc_common.ScriptConfig()

def main():

        argvs = sys.argv  
        argc = len(argvs)
        #ConfigFile="LMCConfig.json"
        #if (argc<1):
        #   # Not enough parameters
        #      print ('Usage: # python %s ConfigJSONFile  ' % argvs[0])
        #      quit()         # プログラムの終了
        #if (argc>1):
        #   ConfigFile=argvs[1] # JSON file
        print(" LMC Initializer from USB memory")
        print(" Start command server or LMC slave")

        # USBからのロード
        USBUpdater(lmcsc)

        # ロガー初期設定
        ###LOGDIR = os.path.join(lmcsc.tmpPath,"log")
        logger = lmc_common.initialize_logger(lmcsc,'logger_command')

        lmc_common.Log("lmcinitializer start",logger)

        lmc_common.Log("create temporary directory",logger)
        # 作業フォルダ作成
        lmc_common.createDirectory(lmcsc.tmpPath)

        # Config File load
        #lmcsc.configLoad()

        # JSON slave config file作成
        print("Create slave config file")
        lmc_common.Log("create slave config file",logger)
        ConfigFile=lmcsc.slaveconfigfilename
        ConfigTempFilePath=os.path.join(lmcsc.tmpPath,ConfigFile)
        ID=lmcsc.get_SlaveID()
        GROUP=lmcsc.SystemGroup
        SlavePatternFile=lmcsc.get_SlavePatternPath()
        LogString= " Pattern file : "+SlavePatternFile
        lmc_common.Log(LogString,logger)
        print (LogString)
        CreateJSONFile(ConfigTempFilePath,ID,GROUP,SlavePatternFile)

        print ("Apply JSON file into LEDMultiControl config file")
        # Compare to existing JSON file and overwrite 
        global absscriptdir
        ConfigFilePath=os.path.join(absscriptdir,ConfigFile)
        
        if not os.path.exists(ConfigFilePath):
           print("Update user temporary json file")
           shutil.copy(ConfigTempFilePath,ConfigFilePath)
        elif not filecmp.cmp(ConfigTempFilePath, ConfigFilePath,False):
           print("Update user temporary json file")
           shutil.copy(ConfigTempFilePath,ConfigFilePath)
        else:
           print("Keep existing user json file")

        #LowPowerMode(lmcsc)
        SetCPUFrequencyMode(lmcsc)

        lmc_common.Log("Setup ended",logger)
        print("Setup ended")

        ## Return Flag : True -> CommandServer False -> Slave
        if (lmcsc.IfMaster):
           LogString="Setup ended. Start command server"
           lmc_common.Log(LogString,logger)
           print (LogString)
           sys.exit(0)

        if not (lmcsc.get_IfSlaveEnabled()):
           LogString="Setup ended. Slave is not enabled. Abort now"
           lmc_common.Log(LogString,logger)
           print (LogString)
           sys.exit(1)

        # Slave also uses command server
        if (lmcsc.IfSlaveCommandServer):
           LogString="Setup ended. Start command server as a slave"
           lmc_common.Log(LogString,logger)
           print (LogString)
           sys.exit(0)

        LogString="Start slave mode"
        lmc_common.Log(LogString,logger)
        print (LogString)

        ## Show Slave ID into LED screen
        NetworkInfo=""
        if (lmcsc.APMODE=='WIFI'):
           NetworkInfo=lmcsc.WIFI_SSID
        else:
           NetworkInfo = lmc_common.ifconfig("eth0")
           if (NetworkInfo==None):
                NetworkInfo=""
        
        ShowString="ID "+str(lmcsc.SlaveID) + "\n"+NetworkInfo
        LogString=ShowString
        lmc_common.Log(LogString,logger)
        print (LogString)

        IoctlSpeed=""
        IoctlFlag=""
        # SPI frequency
        if (lmcsc.LMCType=="LMC"):
           print("LMC04 series")
           IoctlSpeed=""
           IoctlFlag=""
        elif (lmcsc.LMCType=="LMCM"):
           print("LMCM series")
           if (lmcsc.SPIFREQRATIO!=""):
              lmcsc.add_LMCCommandCommonOptions="-ss"+lmcsc.SPIFREQRATIO
           IoctlFlag="-si"
           IoctlSpeed="-ss24"

        Template="-T"+os.path.join(lmcsc.patternPath,lmcsc.patternFile)
        if (lmcsc.IfSilentBoot):
           show_message(["      ",Template,"-ioctl","-at16","-ab64","-S15","-ch","--force","--quiet",IoctlFlag,IoctlSpeed])
        else:
           show_message([ShowString,Template,"-ioctl","-at16","-ab64","-S15","-ch","--force","--quiet",IoctlFlag,IoctlSpeed])

        # Start slave 
        LMCSlavePath=os.path.join(absscriptdir,lmcsc.slavecontrol)
        SlaveCommand=["sudo","nice","-n","-10",LMCSlavePath,"-s","-C"+ConfigFilePath,"-p"+SlavePatternFile,"-w"]
        SlaveCommand.extend(lmcsc.get_LMCCommandCommonOptions())
        SlaveCommand.append("&")
        LogString= "Start LMC slave "
        lmc_common.Log(LogString,logger)
        print (LogString)
        LogString =" ".join(SlaveCommand)
        lmc_common.Log(LogString,logger)
        print (LogString)
        createdsubprocess=subprocess.Popen(SlaveCommand,shell=False)

        LogString= "Slave process started."
        lmc_common.Log(LogString,logger)
        print (LogString)
        createdsubprocess.wait()
        # Wait forever
        while True:
           time.sleep(10)
        sys.exit(1)


def CreateJSONFile(ConfigFilePath,ID,GROUP,SlavePatternFile):

    Variables={}
    #Log(u" CreateJSONFile "+JSONFileName,logger)
    print("CreateJSONFile()")
    Variables["ID"]=ID
    Variables["group"]=GROUP
    #Variables["pattern"]=SlavePatternFile

    FileObject = open(ConfigFilePath , 'w')
    json.dump(Variables,FileObject)
    FileObject.flush()


##################################################################
#
#    RPi power control
#
##################################################################

def LowPowerMode(lmcsc):
    # 低消費電力モード設定
    if (lmcsc.AP_INIT=='INIT'):
        # Full power mode
        #sudo /opt/vc/bin/tvservice -p
        Command=['sudo','/opt/vc/bin/tvservice','-p']
        createdsubprocess=subprocess.Popen(Command,shell=False)
        createdsubprocess.wait()
        print ("HDMI interface ON")
        lmc_common.Log(u"HDMI interface ON",logger)
        #sudo ifconfig wlan0 up
        Command=['sudo','ifconfig','wlan0','up']
        createdsubprocess=subprocess.Popen(Command,shell=False)
        createdsubprocess.wait()
        print ("WLAN ON")
        lmc_common.Log(u"WLAN ON",logger)
        #sudo ifconfig eth0 up
        Command=['sudo','ifconfig','eth0','up']
        createdsubprocess=subprocess.Popen(Command,shell=False)
        createdsubprocess.wait()
        print ("Ethernet ON")
        lmc_common.Log(u"Ethernet ON",logger)
    elif (lmcsc.POWERMODE=='WLAN'):
        #sudo /opt/vc/bin/tvservice -o
        Command=['sudo','/opt/vc/bin/tvservice','-o']
        createdsubprocess=subprocess.Popen(Command,shell=False)
        createdsubprocess.wait()
        print ("HDMI interface OFF")
        lmc_common.Log(u"HDMI interface OFF",logger)
        #sudo ifconfig wlan0 up
        Command=['sudo','ifconfig','wlan0','up']
        createdsubprocess=subprocess.Popen(Command,shell=False)
        createdsubprocess.wait()
        print ("WLAN ON")
        lmc_common.Log(u"WLAN ON",logger)
        #sudo ifconfig eth0 down
        Command=['sudo','ifconfig','eth0','down']
        createdsubprocess=subprocess.Popen(Command,shell=False)
        createdsubprocess.wait()
        print ("Ethernet OFF")
        lmc_common.Log(u"Ethernet OFF",logger)
    elif (lmcsc.POWERMODE=='ETH'):
        Command=['sudo','/opt/vc/bin/tvservice','-o']
        createdsubprocess=subprocess.Popen(Command,shell=False)
        createdsubprocess.wait()
        #sudo ifconfig wlan0 up
        print ("HDMI interface OFF")
        lmc_common.Log(u"HDMI interface OFF",logger)
        Command=['sudo','ifconfig','wlan0','down']
        createdsubprocess=subprocess.Popen(Command,shell=False)
        createdsubprocess.wait()
        print ("WLAN OFF")
        lmc_common.Log(u"WLAN OFF",logger)
        #sudo ifconfig eth0 down
        Command=['sudo','ifconfig','eth0','up']
        createdsubprocess=subprocess.Popen(Command,shell=False)
        createdsubprocess.wait()
        print ("Ethernet ON")
        lmc_common.Log(u"Ethernet ON",logger)
    else:
        Command=['sudo','/opt/vc/bin/tvservice','-p']
        createdsubprocess=subprocess.Popen(Command,shell=False)
        createdsubprocess.wait()
        print ("HDMI interface ON")
        lmc_common.Log(u"HDMI interface ON",logger)
        #sudo ifconfig wlan0 down
        Command=['sudo','ifconfig','wlan0','up']
        createdsubprocess=subprocess.Popen(Command,shell=False)
        createdsubprocess.wait()
        print ("WLAN ON")
        lmc_common.Log(u"WLAN ON",logger)
        #sudo ifconfig eth0 up
        Command=['sudo','ifconfig','eth0','up']
        createdsubprocess=subprocess.Popen(Command,shell=False)
        createdsubprocess.wait()
        print ("Ethernet ON")
        lmc_common.Log(u"Ethernet ON",logger)


def SetCPUFrequencyMode(lmcsc):
   if (lmcsc.CPUFREQMHZ.isnumeric()):
        Command=['sudo','cpufreq-set','-g','userspace']
        createdsubprocess=subprocess.Popen(Command,shell=False)
        createdsubprocess.wait()
        Frequency=lmcsc.CPUFREQMHZ+"Mhz"
        Command=['sudo','cpufreq-set','-f',Frequency]
        createdsubprocess=subprocess.Popen(Command,shell=False)
        createdsubprocess.wait()
        print ("CPUFrequency set to ",lmcsc.CPUFREQMHZ,"MHz")
   else:   
        Command=['sudo','cpufreq-set','-g','performance']
        createdsubprocess=subprocess.Popen(Command,shell=False)
        createdsubprocess.wait()
        print ("CPUFrequency set to full speed mode ")

########################### show_message #########################
# show_message(splitstr)
# 文字をスクロールを表示 
#
###############################################################################
def show_message(splitstr):
    tforceCommand = ""
    OtherOptions = []

    for arg in splitstr:
        #print ("DEBUG : options " , arg)
        if arg.startswith("--force"):
            tforceCommand = "--force"
        elif arg.startswith("-F"):
            continue
        elif arg.startswith("-C"):
            continue
        elif arg.startswith("-backcolor-"):
            continue
        elif arg.startswith("-S"):
            continue
        elif arg.startswith("-PX"):
            #座標指定があった場合 X
            xpos = int(arg.replace('-PX',""))  
        elif arg.startswith("-PY"):
            #座標指定があった場合 Y
            ypos = int(arg.replace('-PY',""))  
        elif arg.startswith("-O"):
            continue
        elif arg.startswith("--"):
            #LEDMultiControlに送らない
            continue
        elif arg.startswith("-"):
            OtherOptions.append(arg)

    #    resultpath = drawmessage.draw_message(splitstr,logger)
    resultpath = drawmessage.draw_messageplain(splitstr,logger)
    if resultpath is None:
        return None

    if DEBUGMODE:
      logmessage= " ".join(["showmessage runnning.",resultpath])
      lmc_common.Log(logmessage,logger)

    FinalCommand=[resultpath]
    FinalCommand.extend(OtherOptions)
    FinalCommand.append(tforceCommand)

    if os.path.isfile(resultpath):
       lmc_common.show_ImageMovieFile(lmcsc,FinalCommand)

    return resultpath

def USBUpdater(lmcsc):

   global absscriptdir

   USBMount="/mnt/usb1"
   USBUpdator=lmcsc.USBUpdator
   USBDevice="/dev/sda"
   USBDevice1="/dev/sda1"
   LMCDirectory=os.path.abspath(os.path.dirname(__file__))
   if not (os.path.exists(USBMount)):
      #sudo mkdir USBMount
      Command=['sudo','mkdir',USBMount]
      print ("Command ", " ".join(Command))
      createdsubprocess=subprocess.Popen(Command,shell=False)
      createdsubprocess.wait()

   if (os.path.exists(USBDevice1)):
      #sudo mount USBDevice,USBMount
      Command=['sudo','mount','-o','iocharset=utf8,ro',USBDevice1,USBMount]
      print ("Command ", " ".join(Command))
      createdsubprocess=subprocess.Popen(Command,shell=False)
      createdsubprocess.wait()
   elif (os.path.exists(USBDevice)):
      #sudo mount USBDevice,USBMount
      Command=['sudo','mount','-o','iocharset=utf8,ro',USBDevice,USBMount]
      print ("Command ", " ".join(Command))
      createdsubprocess=subprocess.Popen(Command,shell=False)
      createdsubprocess.wait()

   #USBが挿入状態を確認
   if os.path.exists(USBUpdator) == False:
        print ("USB memory updator file was not found")
        return

   print ("Firmware update from USB")
   PatternFile=lmcsc.get_PatternFile()
   if (PatternFile!=None):
      Template="-T"+PatternFile
      show_message(["Updating",Template,"-at32","-S12","--force","--quiet"])

   LMCCopyDirectory=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))

   # shutil.copytree(USBPath,LMCPath)
   Command=['sudo','chown','-R','pi:pi',LMCCopyDirectory]
   print ("Modify process  : ", " ".join(Command))
   createdsubprocess=subprocess.Popen(Command,shell=False)
   createdsubprocess.wait()
 
   Command=['sudo','cp','-r','-f',"-u","--preserve=timestamps",USBUpdator,LMCCopyDirectory]
   print ("start copying : ", " ".join(Command))
   createdsubprocess=subprocess.Popen(Command,shell=False)
   createdsubprocess.wait()

   # Auto setup script  /lmc/Autosetup.sh
   AutoSetupPath=os.path.join(LMCDirectory,"autosetup.sh")
   if os.path.exists(AutoSetupPath):
      Command=['sudo','chmod','a+x',AutoSetupPath]
      print ("change mode : ", " ".join(Command))
      createdsubprocess=subprocess.Popen(Command,shell=False)
      createdsubprocess.wait()

      Command=['sudo','-E',AutoSetupPath]
      print ("auto setup : ", " ".join(Command))
      createdsubprocess=subprocess.Popen(Command,shell=False)
      createdsubprocess.wait()

   # lmcsc reload
   lmcsc.configLoad()

   #Setup wireless LAN
   print ("Update WIFI mode from USB")
   wifimanager.WifiUpdate(lmcsc,True)

   subprocess.Popen(["sudo","sync"], shell=False)
   print ("LMC update from USB ended")
   PatternFile=lmcsc.get_PatternFile()
   EndMessage="ID "+str(lmcsc.SlaveID)+"\nUpdate end"
   print ("Pattern file " , PatternFile)
   if (PatternFile!=None):
      Template="-T"+PatternFile
      show_message([EndMessage,Template,"-at32","-S12","--force","--quiet"])

   sys.exit(1)

########################## MAIN #############################

if __name__ == "__main__":

        main()
