#!/usr/bin/env python3
# -*- coding: utf-8 -*-

###########################################################################################
# LMC-01 RPI Tutorial Scripts on Linux-Python
# commandserver.py : LMC Network Command Controller
# Ver.0.3 2016/01/15
# Ver.0.4 2016/02/29
# Ver.0.5 2016/03/22
# Ver.0.6 2017/09/01  by K.Shindo
#
# (C) Kyowa System Co.,ltd. Takafumi Shindo
###########################################################################################

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import socket
import threading
import socketserver
import subprocess
import datetime
import select
import os
import sys
import time
import glob
import pathlib
from traceback import format_tb
import logging
import logging.handlers
import atexit 
import shlex
import shutil
import filecmp
import signal
import base64
#import RPi.GPIO as GPIO
import pigpio

absscriptdir = os.path.abspath(os.path.dirname(__file__))    #絶対ディレクトリの取得　lmcフォルダになる
sys.path.append(absscriptdir)                                                           #スクリプトのルートにパスを通す

import drawmessage
import drawimage
import lmc_common
import wifimanager

lmcsc = lmc_common.ScriptConfig()

#デバッグモードフラグ　出荷時は封じること
DEBUGMODE = True        #False


APPLICATIONLOG = ">>>LMCServer:"
LOGFILENAME = "lmcs_command.log"

COMMANDRESPONSE = "".join(["#################################################\r\n# LMC CommantServer\r\n#################################################\r\n\r\n"])

#作業フォルダ作成
lmc_common.createDirectory(lmcsc.tmpPath)

logger = None

commandListener = None

starttime1 = datetime.datetime.now()

ExitFlag=False
ScheduleFile = ""
IoctlFlag=""
IoctlSpeed=""

FBSW_PIN=17	# GPIO port number

def main():
    global commandListener
    global ScheduleFile

    #初期化中フラグ
    initializing = True
    #print("DEBUG : LMC CommandServer start")
    # Close処理追加
    signal.signal(signal.SIGINT, close)
    # Network Pipe切断通知の無視
    #signal.signal(signal.SIGPIPE,signal.SIG_DFL)

    if (DEBUGMODE):
       ### ロガー初期設定
       #LOGDIR = os.path.join(lmcsc.tmpPath,"log")
       logger = lmc_common.initialize_logger(lmcsc,'logger_command')

    lmc_common.Log(u"".join([u"LMC CommandServer started"]),logger)
    #print("DEBUG : LMC CommandServer started")
 
    #作業フォルダ作成
    #PIDFile Folder Initialize
    pid = os.getpid()

    result = lmc_common.createDirectory(lmcsc.get_PIDRootPath())
    
    booterrorpath = os.path.join(absscriptdir,'LMCError.txt')
    if os.path.exists(booterrorpath):
        os.remove(booterrorpath)
    if "Successful" in result == False:
        f = open(booterrorpath, 'w')
        f.write("RAMDrive creation failed!")
        f.close()

    lmc_common.SetWritePermission(lmcsc.get_PIDRootPath())

    #元プロセスをkillする
    lmc_common.kill_ProcessfromPID(lmcsc.get_PIDPath())
    lmc_common.kill_ProcessfromPID(lmcsc.get_PIDPath_LC())
    lmc_common.kill_ProcessfromPID(lmcsc.get_PIDPath_FTP())
    lmc_common.kill_ProcessfromPID(lmcsc.get_PIDPath_Scheduler())
  
    #自分自身のPIDファイル作成
    f = open(lmcsc.get_PIDPath_LC(),'w')
    f.write(str(pid))
    f.close()


    # Wifi initialize  WifiのUpdateAndRebootの前に設定する
    lmc_common.Log(u"Start wifi mode check",logger)

    # ボタン検出
    #GPIO.setmode(GPIO.BCM)
    #GPIO.setup(FBSW_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    start_pigpio_daemon()
    pi = pigpio.pi()
    pi.set_mode(FBSW_PIN, pigpio.INPUT)
    pi.set_pull_up_down(FBSW_PIN, pigpio.PUD_DOWN)


    #待機時間
    time.sleep(0.1)

    # ボタンチェック
    # P11 GPIO17
#    if GPIO.input(FBSW_PIN) == GPIO.HIGH:
    if pi.read(FBSW_PIN)==1:
       print("LMC FB Mode Switch is ON")
       lmcsc.AP_INIT='INIT'
    else:
       print("LMC FB Mode Switch is OFF")
       lmcsc.AP_INIT='NONE'


    #外部RTCの有効化
    #Command=['sudo','./RTCinit.sh']
    #createdsubprocess=subprocess.Popen(Command,shell=False)
    #createdsubprocess.wait()
 
    #起動画面表示
    #IP取得
    #print ("DEBUG : Start splash screen")
    lmc_common.Log(u"Start splash screen",logger)

    MessageTemplate="-p"+os.path.join(lmcsc.patternPath,lmcsc.patternFile)

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

    ShowString="LMC series\n" 
    ShowString+=lmcsc.AP_SSID

    if not (lmcsc.IfSilentBoot):
        print ("Show start string to LMC " , ShowString)
        show_message([ShowString,MessageTemplate,"-at16","-ab64","-S15","-ch","-sy","-sc","--force","--quiet",IoctlFlag,IoctlSpeed])
        show_message([ShowString,MessageTemplate,"-at16","-ab64","-S15","-ch","--force","--quiet",IoctlFlag,IoctlSpeed])


    # for Access point mode
    #HOST = "10.0.0.120"
    # for slave mode
    #HOST = socket.gethostbyname(socket.gethostname())
    # for another node
    HOST = "0.0.0.0"
    PORT = int(lmcsc.commandPort)
    if not (lmcsc.IfMaster):
        PORT = int(lmcsc.SlaveCommandPort)
    
    # マスタ内スレーブ動作開始。マルチコントロールモード。
    SlaveServerInit(lmcsc)


    print ("Detect network slave nodes")
    # マルチコントロール初期化 スレーブ起動が前提
    lmc_common.ScanCurrentSlaves(lmcsc)
    # 初期状態のMultiPatternパターンを変換 
    print ("Assign to default multi pattern : ",lmcsc.multiPatternFile)
    lmc_common.CreateAssignedMultiPattern(lmcsc,lmcsc.multiPatternFile)

    # Master準備終了 
    #BlackoutScreen(lmcsc,True)

    # スケジューラ動作開始 
    if (lmcsc.AP_INIT=='INIT'):
       lmc_common.Log(u"".join([u"In FB mode, LMC doesn't start scheduler ",""]),logger)
    else :
       lmc_common.Log(u"".join([u"Scheduler start",""]),logger)
       SchedulerRestart(lmcsc)

 
    commandListener = CommandListener(HOST,PORT)
    
    lmc_common.Log(u"".join([u"Command server is ready..",""]),logger)


    if DEBUGMODE:
        lmc_common.Log(u"Start MainLoop",logger)

    global ExitFlag

    while 1:
      time.sleep(0.5)
      if ExitFlag:
          break

    pi.stop()

    return 

########################## CommandListener #############################
# コマンドを受信し応答スレッドを作成する、監視クラス
#
#################################################################################
class CommandListener():
    def __init__(self,HOST,PORT):
      self.stop_event = threading.Event() #停止させるかのフラグ    

      try:
        self.server = socketserver.ThreadingTCPServer((HOST, PORT), ThreadedTCPRequestHandler, False) 
        ip, port = self.server.server_address

      except IOError as ex:
        print (APPLICATIONLOG,"Port[" , str(port) , "]can't Open. CommandServer is Stop.",ex.strerror)
        lmc_common.Log(format_tb(ex.__traceback__)[0],logger)            
        return

      self.server.allow_reuse_address = True 
    
      try:
        self.server.server_bind() 
      except socket.error as se:
        print ("Port[" + str(port) + "] can't Open. CommandServer is Stop.",se.strerror)
        sys.exit()
      self.server.server_activate()
      self.server_thread = threading.Thread(target=self.server.serve_forever)
      #self.server_thread.setDaemon(True)  #Deprecated
      self.server_thread.daemon = True
      self.server_thread.start()

#      print ("Server loop running in thread:", server_thread.getName())

    def stop(self):
        self.server.shutdown()
        self.server_thread.join()
        print (">>>LMCServer:SOCKCOMServer is Finished.")



########################## Parse Recieved Data #############################
# listenerSocket から送り込まれる受信文の解析を行う。
# 受信した文節の中に、コマンドリストに該当する用語の有無を検出、
# 一致すれば、それぞれのコマンドに応じた動作を行う。
#
#  "lmcCmd_" をヘッダとする
#
# string recieve_string
#################################################################################

def descriminate_recievedata(recieve_string,getSocket):

    global ScheduleFile

    decodedBytes = base64.b64decode(recieve_string)
    receivedline=decodedBytes.decode('utf-8')

    receivedline = receivedline.rstrip()
    # command should be all ASCII-> UTF-8
    # File name should be translated SJIS(CP932) into UTF-8 in client softwares.

    logmessage = "RecievedMessage:" + receivedline
    print (logmessage)
    lmc_common.Log(logmessage,logger)
    
    #receivedline=receivedline.replace(chr(0x1f), " ") # for debug
    decodestrArray = lmc_common.CustomizedSplitSpace(receivedline," ",chr(0x1f))
    #print ("DEBUG : Received list" , decodestrArray)
    if len(decodestrArray) == 0:
       getSocket.send("\nReady.\n".encode('UTF-8'))
       return -1

    findstr = u"lmcCmd_"

    if DEBUGMODE:
        lmc_common.Log("findstr encode runnning",logger)

    destinationCommand = decodestrArray[0]
    findcount = destinationCommand.find(findstr)
    if findcount == -1:
        print ("Command not found. " , decodestrArray[0])
        getSocket.send("\nReady.\n".encode('UTF-8'))
        return -1
    
    source = str(decodestrArray[0])[(findcount + len(findstr)):len(decodestrArray[0])]
    del decodestrArray[0]

    if DEBUGMODE:
        logmessage= " ".join(["Converted Command"," ".join(decodestrArray)])
        lmc_common.Log(logmessage,logger)

    #print("Received command  ",source,"End")

    #コマンド分岐
    if source == "reset":
        print ("Start to reset.")

        #元プロセスをkillする
        # Schedulerが最初 
        SchedulerEnd()
        BlackoutScreen(lmcsc,False)

        lmc_common.kill_ProcessfromPID(lmcsc.get_PIDPath())
        lmc_common.kill_ProcessfromPID(lmcsc.get_PIDPath_Thru())
        lmc_common.kill_ProcessfromPID(lmcsc.get_PIDPath_FTP())
        lmc_common.killall_ProcessfromName(lmcsc.get_LEDMultiControlPath())
        #lmc_common.kill_ProcessfromPID(lmcsc.get_PIDPath_Slave())
        lmc_common.WaitUntilLMCEnds(lmcsc,3)
        SlaveServerEnd(lmcsc)

        # Stop audio player
        command=[u"./mplayerstop"]
        subprocess.Popen(command, shell=False)

        # File access
        USBAutoDetector(lmcsc)
        #スレーブ動作開始
        SlaveServerInit(lmcsc)
        #スレーブ再度アサイン準備
        lmc_common.ResetMultiPatternFile(lmcsc)
	#初期化+Blackout
        time.sleep(0.5)
        BlackoutScreen(lmcsc,True)

        getSocket.send("RESET succeeded.".encode())
        getSocket.send("\nReady.\n".encode())
        print ("Ready.")
        #スケジューラ自動再開
        #AutoPlayerTimeoutStart(lmcsc)

    elif source == "connect":
        print ("Connection requested ")
        if len(decodestrArray)>= 1:
           connectiongroup=decodestrArray[0]
           if (connectiongroup == lmcsc.SystemGroup):
              print (" Matched the connection group :",connectiongroup)
              getSocket.send(b"CONNECTED")
           else:
              print (" Connection refused. connection group :",connectiongroup)
              print (" Connection refused. System group :",lmcsc.SystemGroup)
              getSocket.send(b"CONNECTIONREFUSED")
        else:
           getSocket.send("CONNECTED".encode())
        getSocket.send("\nReady.\n".encode())
        print ("Ready.")

    elif source == "watchdog":
        print ("Watch dog request detected ")
        getSocket.send(b"alive")
        
    ###########################################
    ### main command section
    ###########################################

    elif source == "animation":
        # Schedulerを停止していない
        AbortExistingProcess(lmcsc)
        print ("DEBUG   Show Animation: "+decodestrArray[0])
        sendmessage =u"Show Animation:"+decodestrArray[0]+u" start..."
        print (sendmessage)
        Result=lmc_common.show_ImageMovieFile(lmcsc,decodestrArray)
        sendmessage = "Show Animation succeeded."
        getSocket.send(sendmessage.encode('UTF-8'))
        if (Result):
            # if ended normally (NOT loop)
            #print r"DEBUG : Animation process normal end."
            sendmessage = "Showanimation succeeded."
            getSocket.send(sendmessage.encode('UTF-8'))
            getSocket.send("\nReady.\n".encode())
            print ("Ready.")
            AutoPlayerTimeoutStart(lmcsc)
        else:
            print ("Animation process terminated.")
            getSocket.send("\nReady.\n".encode())
            print ("Ready.")

    elif source == "showmessagescroll":
        # Schedulerを停止していない
        AbortExistingProcess(lmcsc)
        Result = show_message(decodestrArray)         
        sendmessage = "Showmessage scroll ended."
        getSocket.send(sendmessage.encode('UTF-8'))
        if (Result):
            # if ended normally (NOT loop)
            sendmessage = "Showmessage succeeded. "
            getSocket.send(sendmessage.encode('UTF-8'))
            getSocket.send("\nReady.\n".encode())
            print ("Ready.")
            AutoPlayerTimeoutStart(lmcsc)
        else:
            print ("Showmessage process terminated.")
            getSocket.send("\nReady.\n".encode())
            print ("Ready.")

    elif source == "showimagescroll":
        # Schedulerを停止していない
        AbortExistingProcess(lmcsc)
        Result = draw_image(decodestrArray)
        sendmessage = "Showimage scroll ended."
        getSocket.send(sendmessage.encode('UTF-8'))
        if (Result):
            # if ended normally (NOT loop)
            print (" showimagescroll normal end.")
            sendmessage = "Showimage succeeded. "
            getSocket.send(sendmessage.encode('UTF-8'))
            getSocket.send("\nReady.\n".encode())
            print ("Ready.")
            AutoPlayerTimeoutStart(lmcsc)
        else:
            print ("Showimage process terminated.")
            getSocket.send("\nReady.\n".encode())
            print ("Ready.")

    elif source == "showmessage":
        # Schedulerを停止していない
        AbortExistingProcess(lmcsc)
        Result = show_message(decodestrArray)         
        sendmessage = "Showmessage succeeded. "
        getSocket.send(sendmessage.encode('UTF-8'))
        getSocket.send("\nNormalEnd.".encode())
        getSocket.send("\nReady.\n".encode())
        print ("Ready.")
        # no timeout

    elif source == "showimage":
        # Schedulerを停止していない
        AbortExistingProcess(lmcsc)
        Result = draw_image(decodestrArray)
        sendmessage = "Showimage succeeded. "
        getSocket.send(sendmessage.encode('UTF-8'))
        getSocket.send("\nNormalEnd.".encode())
        getSocket.send("\nReady.\n".encode())
        print ("Ready.")
        # no timeout

    elif source == "abort":
        # Scheduler停止 
        print ("abort request.")
        SchedulerEnd()
        AbortExistingProcess(lmcsc)
        BlackoutScreen(lmcsc,False)
        sendmessage = "Abort succeeded."
        getSocket.send(sendmessage.encode('UTF-8'))
        getSocket.send("\nReady.\n".encode())
        print ("Ready.")
        # Scheduler再開
        AutoPlayerTimeoutStart(lmcsc)

    elif source == "stop":
        print ("stop request.")
        # Scheduler停止 
        SchedulerEnd()
        AbortExistingProcess(lmcsc)
        # Blackoutは行わない

        sendmessage = "Stop succeeded."
        getSocket.send(sendmessage.encode('UTF-8'))
        getSocket.send("\nReady.\n".encode())
        print ("Ready.")
        # no timeout

    elif source == "blackout":
        # Schedulerを停止していない
        AbortExistingProcess(lmcsc)
        BlackoutScreen(lmcsc,False)
        sendmessage = "Blackout succeeded."
        getSocket.send(sendmessage.encode('UTF-8'))
        getSocket.send("\nReady.\n".encode())
        print ("Ready.")
        # no timeout

    ###########################################
    ### data access section
    ###########################################

    elif source == "filelist":
        #FileList取得、文字列として書き戻す
        print ("Get","'get_FileList'","Command...")
        result = [r"IMAGEFILE LIST"]
        result = lmc_common.getfilelist(lmcsc.get_FTPRoot(),result)
        result = lmc_common.getfilelist(lmcsc.get_LocalImagePath(),result)
        result = lmc_common.getfilelist(lmcsc.get_USBImagePath(),result)
        
        sendmessage = "\n".join(result)
        
        print (sendmessage)

        getSocket.send(sendmessage.encode('UTF-8'))
        getSocket.send("\nReady.\n".encode())
        print ("Ready.")

    elif source == "fontlist":
        res = exec_cmd(u"fc-list")
        result = [r"AVAILABLEFONTS LIST"]
        for s in res:
            if ".ttf" in s or ".ttc" in s or ".otf" in s:
                splitted = s.split(":")
                result.append(splitted[0])
        sendmessage ="\n".join(result)
        print (sendmessage)
        getSocket.send(sendmessage.encode('UTF-8'))
        getSocket.send("\nReady.\n".encode())
        print ("Ready.")

    elif source == "patternlist":
        result = [u"PATTERNFILE LIST"]
        result = lmc_common.getfilelist(lmcsc.get_FTPRoot(), result)
        result = lmc_common.getfilelist(lmcsc.patternPath,result)
        result = lmc_common.getfilelist(lmcsc.get_USBImagePath(),result)
        sendmessage ="\n".join(result)
        print (sendmessage)
        getSocket.send(sendmessage.encode('UTF-8'))
        getSocket.send("\nReady.\n".encode())
        print ("Ready.")

    elif source == "showip":
        #自分自身のIPとIDを知らせる
        HostNameList=socket.gethostbyname_ex(socket.gethostname())
        print (HostNameList)
        IPList=HostNameList[2]
        receive = u"Hostname "+HostNameList[0]+" "
        receive += u"IPaddress "
        receive += " ".join(IPList)
        print (receive)
        getSocket.send(receive.encode('UTF-8'))
        getSocket.send("\nReady.\n".encode())
        print ("Ready.")

    elif source == "showfilefreespace":
        freespacesize=lmc_common.GetDiskFreespace()
        receive = u"Freespace\n"+str(freespacesize)
        print(receive)
        getSocket.send(receive.encode('UTF-8'))
        getSocket.send("\nReady.\n".encode())
        print ("Ready.")

    elif source == "cleartmpdir":
        #テンポラリフォルダの中身をクリア FTPフォルダをクリアするわけではないことに注意
        destination = lmcsc.get_TempImagePath()
        shutil.rmtree(destination,True)
        lmc_common.createDirectory(destination)
        sendmessage = u"".join([u"Deleted temporary files : ",destination])
        print (sendmessage)
        getSocket.send(sendmessage.encode('UTF-8'))
        getSocket.send("\nReady.\n".encode())
        print ("Ready.")

    elif source == "configdump":
        ResultList=lmcsc.dumpConfigScripts()
        result = [u"config dump\n"]
        if (len(ResultList)>0):
           for ResultLine in ResultList:
              result+=ResultLine
              result+=u"\n"
              getSocket.send(ResultLine.encode('UTF-8'))
        getSocket.send("\nReady.\n".encode())
        print ("Ready.")
        
    elif source == "configget":
        # Configurationの中身を読み出す
        if len(decodestrArray)>= 2:
           print ("config read parameter :",decodestrArray[0],decodestrArray[1])
           lmcsc.loadConfigFile()
           ReturnValue = lmcsc.getSpecifiedConfig(decodestrArray[0],decodestrArray[1])
           if (ReturnValue==None):
                sendmessage=u"config read failed."
                print (sendmessage)
                getSocket.send(sendmessage.encode('UTF-8'))
           else:
                sendmessage=u"CONFIGGET\n"
                sendmessage+= u" ".join([decodestrArray[0],decodestrArray[1],ReturnValue])
                print (sendmessage)
                getSocket.send(sendmessage.encode('UTF-8'))
        getSocket.send("\nReady.\n".encode())
        print ("Ready.")

    elif source == "configset":
        # Configurationの中身を改変する
        if len(decodestrArray) >= 2:
           Value=""
           if len(decodestrArray) >= 3:
               Value=decodestrArray[2]
           print ("config write parameter :",decodestrArray[0],decodestrArray[1]," Value : ",Value)
           ReturnValue=lmcsc.setSpecifiedConfig(decodestrArray[0],decodestrArray[1],Value)
           ReturnValue&=lmcsc.saveConfigFile()
           if (ReturnValue):
               sendmessage=u"config set succeeded."
           else:
               sendmessage=u"config set failed."
           print (sendmessage)
           getSocket.send(sendmessage.encode('UTF-8'))
        getSocket.send("\nReady.\n".encode())
        print ("Ready.")
    elif source == "configreload":
        # Reload config file
        lmcsc.configLoad()
        print ("Config file reloaded.")
        getSocket.send("\nReady.\n".encode())
        print ("Ready.")

    elif source == "date":
        # 日付の改変
        if len(decodestrArray)>= 1:
           DecodedDate=decodestrArray[0].lstrip('"\'')
           DecodedDate=DecodedDate.rstrip('"\'')
           command=[u"sudo",u"date",u"-s",DecodedDate]
           subprocess.Popen(command, shell=False)
           command=[u"date",u"--rfc-3339=seconds"]
           Result=subprocess.check_output(command, shell=False)
           Result=Result.decode()
           print ("Time Modeified : " , Result)
           getSocket.send(("TimeModified: "+Result).encode('UTF-8'))

        getSocket.send("\nReady.\n".encode())
        print ("Ready." )

    ###########################################
    ### Remote server section
    ###########################################

    elif source == "slavestart":
        # 
        #SchedulerEnd()
        #BlackoutScreen(lmcsc,False)
        #SlaveServerEnd(lmcsc)
        currentPatternPath=os.path.join(lmcsc.patternPath,lmcsc.patternFile)
        OtherOptions = []
        if len(decodestrArray)> 0:
          for arg in decodestrArray:
            print(arg)
            if arg.startswith("-p"):
                tmpPatternPath = arg.replace('-p',"")
                print( "Specified template " , tmpPatternPath)
                FoundPath=lmc_common.SearchPatternFromFile(lmcsc,tmpPatternPath)
                if (FoundPath!=""):
                    currentPatternPath=FoundPath
            else:
                OtherOptions.append(arg)
                print ("Other options" ,arg)

        SlaveServerStart(lmcsc,currentPatternPath,OtherOptions)


        getSocket.send(b"Slave server started.")
        getSocket.send("\nReady.\n".encode())
        print ("Ready.")

    elif source == "slaveend":
        SlaveServerEnd(lmcsc)
        getSocket.send(b"Slave server ended.")
        getSocket.send("\nReady.\n".encode())
        print ("Ready.")

    elif source == "remoteslavestart":
        # Single時専用Slave起動。Multiの時のSlaveは無関係に起動される。 
        # 結果的にslavestartとの違いはない。
        currentPatternPath=os.path.join(lmcsc.patternPath,lmcsc.patternFile)
        OtherOptions = []
        if len(decodestrArray)> 0:
          for arg in decodestrArray:
            print(arg)
            if arg.startswith("-p"):
                tmpPatternPath = arg.replace('-p',"")
                print( "Specified template " , tmpPatternPath)
                FoundPath=lmc_common.SearchPatternFromFile(lmcsc,tmpPatternPath)
                if (FoundPath!=""):
                    currentPatternPath=FoundPath
            else:
                OtherOptions.append(arg)
                print ("Other options" ,arg)

        SlaveServerStart(lmcsc,currentPatternPath,OtherOptions)
        getSocket.send(b"Slave server started.")
        getSocket.send("\nReady.\n".encode())
        print ("Ready.")

    elif source == "remoteslaveend":
        # Multiの時のSlaveには作用しない。　
        RemoteSlaveServerAbort(lmcsc)
        getSocket.send("\nReady.\n".encode())
        print ("Ready.")

    ###########################################
    ### scheduler section
    ###########################################

    elif source == "schedulerstart":
        # スレーブ動作開始。マルチコントロールモード。
        SlaveServerInit(lmcsc)
        ScheduleFile=lmcsc.get_SchedulerFilePath()
        if len(decodestrArray)> 0:
          ScheduleFile=decodestrArray[0]

        if (SchedulerStart(lmcsc,ScheduleFile)):
           getSocket.send(b"Scheduler started.")
           print ("Scheduler started.")
        getSocket.send("\nReady.\n".encode())
        print ("Ready.")

    elif source == "schedulerrunning":
        PIDPath=lmcsc.get_PIDPath_Scheduler()
        if os.path.exists(PIDPath):
           sendmessage=u"Schedulerisrunning\n"+ScheduleFile
           getSocket.send(sendmessage.encode('UTF-8'))
           print ("Scheduler is running : ",ScheduleFile)
        else:
           getSocket.send(b"Schedulerisstopped")
           print ("Scheduler stopped ")
        getSocket.send("\nReady.\n".encode())
        print ("Ready.")

    elif source == "schedulertimeoutstart":
        getSocket.send(b"Scheduler starts from timeout.")
        getSocket.send("\nReady.\n".encode())
        AutoPlayerTimeoutStart(lmcsc)
        print ("Ready.")

    elif source == "schedulerend":
        SchedulerEnd()
        BlackoutScreen(lmcsc,False)
        getSocket.send(b"Scheduler ended.")
        getSocket.send("\nReady.\n".encode())
        print ("Ready.")

    elif source == "ftpreboot":
        command_FTPReboot(lmcsc)
        getSocket.send(b"FTP server started.")
        getSocket.send("\nReady.\n".encode())
        print ("Ready.")

    elif source == "ftpkill":
        command_FTPKill(lmcsc)
        sendmessage = u"".join([u"FTP server ended."])
        getSocket.send(sendmessage.encode('UTF-8'))
        getSocket.send("\nReady.\n".encode())
        print ("Ready.")

    ###########################################
    ### file manager section
    ###########################################

    elif source == "removefile":
        if len(decodestrArray)>0:
           RemoveFile=decodestrArray[0]
           path  = lmc_common.SearchGeneralFile(lmcsc,RemoveFile)
           if path!="":
              print ("Removing file : " , path)
              Command=['sudo','rm','-f',path]
              createdsubprocess=subprocess.Popen(Command,shell=False)
              createdsubprocess.wait()
              #os.remove(path)
              getSocket.send(b"File removed.")
        getSocket.send("\nReady.\n".encode())
        print ("Ready.")

    elif source == "movefile":
        if len(decodestrArray)>1:
           moveFile=decodestrArray[0]
           path  = lmc_common.SearchGeneralFile(lmcsc,moveFile)
           if path!="":
              targetfile=decodestrArray[1]
              targetfilename=targetfile.strip("'")
              pathtarget=os.path.join(lmcsc.get_FTPRoot(),targetfilename)
              #moveTargetPath=lmc_common.TranslateIntoUTF8(pathtarget)
              print ("Moving file : " , path," into " , pathtarget)
              Command=['sudo','mv','-f',path,pathtarget]
              createdsubprocess=subprocess.Popen(Command,shell=False)
              createdsubprocess.wait()
              #shutil.move(path,pathtarget)
              getSocket.send(b"File move ended.")
        getSocket.send("\nReady.\n".encode())
        print ("Ready.")
    elif source == "movetopatternfile":
        if len(decodestrArray)>0:
           moveFile=decodestrArray[0]
           path  = lmc_common.SearchGeneralFile(lmcsc,moveFile)
           if path!="":
              print ("Moving file : " , path," into " , lmcsc.patternPath)
              Command=['sudo','mv','-f',path, lmcsc.patternPath]
              createdsubprocess=subprocess.Popen(Command,shell=False)
              createdsubprocess.wait()
              #shutil.move(path,pathtarget)
              getSocket.send(b"File move ended.")
        getSocket.send("\nReady.\n".encode())
        print ("Ready.")
    elif source == "addwritepermission":
        if len(decodestrArray)>0:
           ApplyingFile=decodestrArray[0]
           path  = lmc_common.SearchGeneralFile(lmcsc,ApplyingFile)
           if path!="":
              print ("Add write permission into file : " , path)
              createdsubprocess=subprocess.Popen(["sudo","chmod","a+w",path], shell=False)
              createdsubprocess.wait()
              getSocket.send(b"Permission modified.")
        getSocket.send("\nReady.\n".encode())
        print ("Ready.")

    elif source == "remote":
        # Remote shell execution
        # NOT use UTF-8 file name
        if len(decodestrArray)>0:
           ### Remove path. Execute only on current path.
           ExecutingFile=os.path.basename(decodestrArray[0])
           ExecutingFile=os.path.join(os.getcwd(),ExecutingFile)
           decodestrArray[0]=ExecutingFile
           print ("Remote execution command : " , decodestrArray)
           createdsubprocess=subprocess.Popen(decodestrArray, shell=False)
           createdsubprocess.wait()
           getSocket.send(b"Shell executed.")
        getSocket.send("\nReady.\n".encode())
        print ("Ready.")
    ###########################################
    ### wifi section
    ###########################################

    elif source == "wifiupdate":
        # ボタンチェック
        # P11 GPIO17
        #if GPIO.input(FBSW_PIN) == GPIO.HIGH:
        if pi.read(FBSW_PIN) == 1:
          print ("LMC Mode Switch is ON")
          lmcsc.AP_INIT='INIT'
        else:
          print ("LMC Mode Switch is OFF")
          lmcsc.AP_INIT='NONE'

        IfBoot=wifimanager.WifiUpdate(lmcsc)
        getSocket.send("\nReady.\n".encode())
        print ("Ready.")

    ###########################################
    ### Multicontrol configuration section
    ###########################################

    elif source == "slave_createpattern":
        # マルチコントロール初期化 スレーブ起動が前提
        lmc_common.ScanCurrentSlaves(lmcsc)
        # 初期状態のMultiPatternパターンを変換 
        MultiPatternFile=lmcsc.multiPatternFile
        if len(decodestrArray)>0:
           MultiPatternFile=decodestrArray[0]
        print ("Assign to default multi pattern : ",MultiPatternFile)
        lmc_common.CreateAssignedMultiPattern(lmcsc,MultiPatternFile)

        # Set Original pattern
        getSocket.send("\nReady.\n".encode())
        print ("Ready.")

    elif source == "slave_idassign":
        MultiConfigName=lmcsc.get_MultiConfigPath()
        
        createdsubprocess=subprocess.Popen(["sudo","python3","lmcJSONtolanIDassign.py",MultiConfigName], shell=False)
        createdsubprocess.wait()
        getSocket.send("\nReady.\n".encode())
        print ("Ready.")

  

    ###########################################
    ### epilogue section
    ###########################################

    elif source == "shutdown":
        # Reset Schedulerが最初 
        SchedulerEnd()
        BlackoutScreen(lmcsc,False)
        lmc_common.kill_ProcessfromPID(lmcsc.get_PIDPath())
        lmc_common.kill_ProcessfromPID(lmcsc.get_PIDPath_Thru())
        lmc_common.kill_ProcessfromPID(lmcsc.get_PIDPath_FTP())
        lmc_common.killall_ProcessfromName(lmcsc.get_LEDMultiControlPath())
        lmc_common.kill_ProcessfromPID(lmcsc.get_PIDPath_Slave())
        lmc_common.WaitUntilLMCEnds(lmcsc,3)

        getSocket.send(b"Shutdown started.")
        print ("LMC Shutdown")
        MessageTemplate="-p"+os.path.join(lmcsc.patternPath,lmcsc.patternFile)
        show_message(["Shutdown",MessageTemplate,"-at32","-S12","--force","--quiet",IoctlFlag,IoctlSpeed])

        subprocess.Popen(["sudo","shutdown","now"], shell=False)
        getSocket.send(b"SHUTDOWN")
        print ("SHUTDOWN.")
        ExitFlag=True

    elif source == "reboot":
        MessageTemplate="-p"+os.path.join(lmcsc.patternPath,lmcsc.patternFile)
        show_message(["Rebooting",MessageTemplate,"-at32","-S12","--force","--quiet",IoctlFlag,IoctlSpeed])

        getSocket.send(b"Reboot started.")
        print ("LMC Reboot")
        #待機時間
        time.sleep(1)
        subprocess.Popen(["sudo","reboot"], shell=False)
        getSocket.send("\nREBOOT".encode())
        print ("REBOOT")
        ExitFlag=True

    elif source == "exit":
        getSocket.send(b"Command server ended.")
        print ("LMC command server end\n")
        ExitFlag=True
        print ("Ready.")

    else:
        print ("Undefined command : "+source)
        getSocket.send("\nReady.\n".encode())
        print ("Ready.")




########################### Task #########################
#
###############################################################################

def exec_cmd(cmd):
    from subprocess import Popen, PIPE

    p = Popen(cmd.split(u' '), stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()

    return [s.decode('utf-8') for s in out.split(b'\n') if s]



########################### draw_image #########################
# draw_image(splitstr)
# 未フォーマットの画像を表示 パラメータはdrawgianimation.pyと同様の仕様
#
###############################################################################
def draw_image(splitstr):

    tLOOPCOUNT = "-I1"
    OtherOptions = []
    for arg in splitstr:
        if arg.startswith("-I"):
            continue
        elif arg.startswith("--"):
            #LEDMultiControlに送らない
            continue
        elif arg.startswith("-"):
            OtherOptions.append(arg)


    resultpath = drawimage.draw_image(splitstr)
    if resultpath is None:
        return None

    FinalCommand=[resultpath]
    FinalCommand.extend(OtherOptions)

    Result=False
    if os.path.isfile(resultpath):
       Result=lmc_common.show_ImageMovieFile(lmcsc,FinalCommand)

    return Result


########################### show_message #########################
# show_message(splitstr)
# 文字をスクロールを表示 パラメータはscrollmesdraw.pyと同様の仕様
#
###############################################################################
def show_message(splitstr):

    OtherOptions = []

    for arg in splitstr:
        if arg.startswith("-F"):
            continue
        elif arg.startswith("-C"):
            continue
        elif arg.startswith("-backcolor-"):
            continue
        elif arg.startswith("-S"):
            continue
        elif arg.startswith("-PX"):
            continue
        elif arg.startswith("-PY"):
            continue
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

    Result=False
    if os.path.isfile(resultpath):
       Result=lmc_common.show_ImageMovieFile(lmcsc,FinalCommand)

    return Result


########################## command_FTPReboot #############################
#  FTPサーバの再起動を行う。ltsCmd_ftpreboot で呼び出され、ftpサーバの再起動を行う。
#　FTPサーバが動作していれば /tmp/ltmServer/pid/ltmftp.pid が存在するはずなので、
#　これをKILLしてからサーバスクリプトを呼び出す。
#################################################################################

def command_FTPReboot(lmcsc):
    
    print(">>>LMCServer(COM):Get command 'Reboot FTPServer'..." )

    lmc_common.kill_ProcessfromPID(lmcsc.get_PIDPath_FTP())
    
    ftppath = os.path.join(lmcsc.lmcHomePath,"ftpserver.py")
    spcommand = ["sudo","python3",ftppath]
    createdsubprocess=subprocess.Popen(spcommand, shell=False)
    print(">>>LMCServer(COM):FTPServer was reboot now." )

def command_FTPKill(lmcsc):

    print(">>>LMCServer(COM):Get command 'Kill FTPServer'..." )
    print(lmcsc.get_PIDPath_FTP())

    lmc_common.kill_ProcessfromPID(lmcsc.get_PIDPath_FTP())

    print(">>>LMCServer(COM):FTPServer is killed now." )

########################### Scheduler #########################
#   scheduler.txtがあれば、Schedulerを起動
#   すでにPIDファイルがあるならば、Schedulerは動作中なので二重起動しない。
###############################################################################
def SchedulerStart(lmcsc,ScheduleFile):

    PIDPath=lmcsc.get_PIDPath_Scheduler()
    if os.path.exists(PIDPath):
        #動作中
        return False

    # Kill process
    lmc_common.kill_ProcessfromPID(lmcsc.get_PIDPath_Scheduler())
    lmc_common.WaitUntilSchedulerEnds(5)

    #print ("DEBUG FTPRoot" ,lmcsc.get_FTPRoot())
    #print ("DEBUG ScheduleFile ",ScheduleFile)
    schedulerpath = os.path.join(lmcsc.lmcHomePath,lmcsc.get_SchedulerPath())
    filepath = os.path.join(lmcsc.get_FTPRoot(),ScheduleFile)
    print (" Scheduler start :",filepath)
    if os.path.exists(filepath):
       commandList =["sudo","python3",schedulerpath,filepath,PIDPath]
       print (" Scheduler start :",filepath)
       subprocess.Popen(commandList, shell=False)
       return True

    return False

def SchedulerRestart(lmcsc):
    if (USBautoplayer(lmcsc)):
        return
    ##
    ScheduleFile=lmcsc.get_SchedulerFilePath()
    if (SchedulerStart(lmcsc,ScheduleFile)):
        print ("Scheduler started.")


def SchedulerEnd():
    PIDPath=lmcsc.get_PIDPath_Scheduler()
    if os.path.exists(PIDPath):
       # Kill process
       lmc_common.kill_ProcessfromPID(lmcsc.get_PIDPath_Scheduler())
       lmc_common.killall_ProcessfromName(lmcsc.get_LEDMultiControlPath())
       # 待機時間
       lmc_common.WaitUntilSchedulerEnds(5)
       # LMC終了
       lmc_common.stop_ProcessfromPID(lmcsc.get_PIDPath())
       # LMC待機時間
       lmc_common.WaitUntilLMCEnds(lmcsc,3)


def AutoPlayerTimeoutStart(lmcsc):
    i=0
    TimeoutSeconds=5
    WaitCount=TimeoutSeconds*10
    IfProcessStarted=False
    print ("Waiting for timeout for ",TimeoutSeconds," seconds")
    print (" to start default scheduler.")
    for i in range(1,WaitCount):
        if lmc_common.CheckLMCisStillRunning(lmcsc):
              IfProcessStarted=True
              break
        if lmc_common.CheckSchedulerisStillRunning():
              IfProcessStarted=True
              break
        time.sleep(0.1)
    if (IfProcessStarted):
        return
    else:
        print ("Scheduler start from timeout.")
        SchedulerRestart(lmcsc)


########################### LMC process #########################
###############################################################################

def AbortExistingProcess(lmcsc):
    # 現在実行中のプロセスを終了。 Slave,ThruServerは消去。Schedulerは別のところで消去。

    lmc_common.stop_ProcessfromPID(lmcsc.get_PIDPath())
    #lmc_common.killall_ProcessfromName(lmcsc.get_LEDMultiControlPath())
    RemoteSlaveServerAbort(lmcsc)
    lmc_common.WaitUntilLMCEnds(lmcsc,3)
    time.sleep(0.1)

def BlackoutScreen(lmcsc,IfReset):
       # Blackout
       FinalCommand=[]
       if (lmcsc.multiPatternFile!=""):
           FinalCommand.append('-m')
       if not IfReset:
          FinalCommand.append('-w')
       lmc_common.show_ImageMovieFile(lmcsc,FinalCommand)




########################### Slave server #########################
###############################################################################

def SlaveServerInit(lmcsc):
    

   # スレーブ動作開始。マルチモード専用。
    print ("PatternFile",lmcsc.patternFile)
    print ("MultiPatternFile : ",lmcsc.multiPatternFile)
    print ("Slave enabled ",lmcsc.get_IfSlaveEnabled())
    if (lmcsc.get_IfSlaveEnabled()):
       if (lmcsc.patternFile!=""):
          if (lmcsc.multiPatternFile!=""):
              SlaveServerStart(lmcsc,"",[])


def SlaveServerStart(lmcsc,currentPatternPath,OtherOptions):

        LMCSlavePath=os.path.join(absscriptdir,lmcsc.slavecontrol)
        slvPidPath = lmcsc.get_PIDPath_Slave()
        command_slvPidPath = "-P"+slvPidPath
        ConfigFile=lmcsc.slaveconfigfilename
        ConfigFilePath=os.path.join(absscriptdir,ConfigFile)

        if (currentPatternPath==""):
           currentPatternPath=os.path.join(lmcsc.patternPath,lmcsc.patternFile)

        #実行中プロセスを停止する
        lmc_common.stop_ProcessfromPID(lmcsc.get_PIDPath())
        lmc_common.killall_ProcessfromName(lmcsc.get_LEDMultiControlPath())
        lmc_common.WaitUntilLMCEnds(lmcsc,3)

        #古いスレーヴコントローラを強制終了
        lmc_common.stop_ProcessfromPID(slvPidPath,IfNetworking=True)

        Options =["sudo","nice","-n","-10",LMCSlavePath,"-s","-p"+currentPatternPath,"-C"+ConfigFilePath]
        Options.extend(OtherOptions)
        Options.append(command_slvPidPath)
        Options.extend(lmcsc.get_LMCCommandCommonOptions())
        Options.append("&")
        #command = " ".join(Options)

        print ("Slave start.",Options)
        #print (command)
        #subprocess.Popen(shlex.split(command), shell=False)
        subprocess.Popen(Options,shell=False)

        PIDPath=lmcsc.get_PIDPath_Slave()
        if os.path.exists(PIDPath):
           #動作中
           return False
        
        return True

def SlaveServerEnd(lmcsc):
        #古いスレーヴコントローラを強制終了
        print ("Slave server end.")
        lmc_common.stop_ProcessfromPID(lmcsc.get_PIDPath_Slave(),IfNetworking=True)
        lmc_common.WaitUntilLMCSlaveEnds(lmcsc,5)

def RemoteSlaveServerAbort(lmcsc):
        #古いスレーヴコントローラを強制終了 Masterなら停止しない。
        #if (lmcsc.get_IfSlaveEnabled()):
        IfStopSlave=False
        IfSlaveEnabled=lmcsc.get_IfSlaveEnabled()
        if not IfSlaveEnabled:
             print ("Temporary slave server abort")
             # Single remote slave server ... abort
             lmc_common.stop_ProcessfromPID(lmcsc.get_PIDPath_Slave(),IfNetworking=True)
             lmc_common.WaitUntilLMCSlaveEnds(lmcsc,5)

def ThruServerStart(lmcsc,currentPatternPath,OtherOptions):

        ThruMasterControlAppPath= lmcsc.thrucontrol
        thruPidPath = lmcsc.get_PIDPath_Thru()
        command_thruPidPath = "-P"+thruPidPath

        if (currentPatternPath==""):
           currentPatternPath=os.path.join(lmcsc.patternPath,lmcsc.multiPatternFile)

        #実行中プロセスを停止する
        lmc_common.stop_ProcessfromPID(lmcsc.get_PIDPath())
        #lmc_common.killall_ProcessfromName(lmcsc.get_LEDMultiControlPath())
      
        #古いスル―マスターコントローラを強制終了
        lmc_common.kill_ProcessfromPID(thruPidPath)
        
        lmc_common.WaitUntilLMCEnds(lmcsc,3)

        Options=[u"nice",u"-n",u"-10",ThruMasterControlAppPath,u"-ms",u"-t"+currentPatternPath]
        Options.extend(OtherOptions)
        Options.append(command_thruPidPath)
#       Options.append(u"-L")   # for debug
        Options.append(u"&")
        #command = " ".join(Options)

        print ("Thru server started.")
        #print (command)
        #subprocess.Popen(shlex.split(command), shell=False)
        subprocess.Popen(Options, shell=False)

        return True

#############  automatic play from USB ########################
#########################################################################

def USBautoplayer(lmcsc):

   print ("Try to start USB auto player")

   USBMount="/mnt/usb1"
   if not os.path.exists(USBMount):
      if (USBAutoDetector(lmcsc) == False):
         print ("USB memory not detected")
         return False

   ## Scan MP4
   USBMount="/mnt/usb1"
   FileSearchPath=os.path.join(USBMount,"*.*")
   FileList=glob.glob(FileSearchPath)
   CommandPort = lmcsc.commandPort
   CommandHost= socket.gethostbyname(socket.gethostname())

   for FoundFile in FileList :

           print ("DEBUG current found file ",FoundFile)

           ## Show movie
           if (SchedulerFileDetector(lmcsc,FoundFile)):
              AbortExistingProcess(lmcsc)
              print ("DEBUG   Start scheduler: ",FoundFile)
              SchedulerStart(lmcsc,FoundFile)
              return
           
           ## Show movie
           if (MovieFileDetector(lmcsc,FoundFile)):
              AbortExistingProcess(lmcsc)
              sendmessage =u"Show Animation:"+FoundFile+" start..."
              print (sendmessage)
              FileName="".join(["'",FoundFile,"'"])
              SplitCommand=["lmcCmd_animation",FileName]
              SplitCommand.extend(CreateCommand(lmcsc))
              SplitCommand.append("-i0")
              SplitCommand.append("-mo")
              print ("DEBUG : Show option" ,SplitCommand)
              RemoteCommand="'"+(" ".join(SplitCommand))+"'"
              commandList =["sudo","python3","lmccommandclient.py",CommandHost,CommandPort]
              commandList.append(" ".join(SplitCommand))
              print (" remote command start :",commandList)
              subprocess.Popen(commandList, shell=False)

              sendmessage = "Show Animation succeeded."
              return True
           
           ## Show image
           if (ImageFileDetector(lmcsc,FoundFile)):
              AbortExistingProcess(lmcsc)
              sendmessage =u"Show Image:"+FoundFile+" start..."
              print (sendmessage)
              FileName="".join(["'",FoundFile,"'"])
              SplitCommand=["lmcCmd_showimage",FileName]
              SplitCommand.extend(CreateCommand(lmcsc))
              print ("DEBUG : Show option" ,SplitCommand)
              RemoteCommand="'"+(" ".join(SplitCommand))+"'"
              commandList =["sudo","python3","lmccommandclient.py",CommandHost,CommandPort]
              commandList.append(" ".join(SplitCommand))
              print (" remote command start :",commandList)
              subprocess.Popen(commandList, shell=False)

              sendmessage = "Show Image succeeded."
              return True

   return False


   
def MovieFileDetector(lmcsc,FoundFile):
    path=pathlib.Path(FoundFile)
    Suffix=path.suffix
    Suffix=Suffix.upper()
    print ("DEBUG file suffix ",Suffix)
    if (Suffix==".MP4"):
       return True
    elif (Suffix==".MOV"):
       return True
    elif (Suffix==".WMV"):
       return True
    elif (Suffix==".MPG"):
       return True
    elif (Suffix==".AVI"):
       return True
    elif (Suffix==".MKV"):
       return True
    elif (Suffix==".WEBM"):
       return True

    return False

def ImageFileDetector(lmcsc,FoundFile):
    path=pathlib.Path(FoundFile)
    Suffix=path.suffix
    Suffix=Suffix.upper()
    if (Suffix==".JPG"):
       return True
    elif (Suffix==".JPEG"):
       return True
    elif (Suffix==".BMP"):
       return True
    elif (Suffix==".PNG"):
       return True

    return False


def SchedulerFileDetector(lmcsc,FoundFile):
    path=pathlib.Path(FoundFile)
    Suffix=path.suffix
    Suffix=Suffix.upper()
    if (Suffix==".SCD"):
       return True

    return False

def USBAutoDetector(lmcsc):

   global absscriptdir

   USBMount="/mnt/usb1"
   USBDevice="/dev/sda"
   USBDevice1="/dev/sda1"
 
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
   if os.path.exists(USBMount) == False:
        print ("USB memory not found")
        return False

   print ("Found USB memory")
   return True

def CreateCommand(lmcsc):
   Options=[]
   Brightness=lmcsc.brightness
   Options.append("-ab"+Brightness)
   CoeffLimit=lmcsc.brightnesslimit
   Options.append("-at"+CoeffLimit)
   if (lmcsc.multiPatternFile!=""):
      Options.append("-m")

   return Options


########################## onClosing #############################

def close(num, frame):

    global commandListener

    lmc_common.Log(u"".join([u">>>LTMServer:",u"Finished"]),logger)

    commandListener.stop()

    print (">>>LMCServer:CommandServer is Finished Completely. ")

    threadlist = threading.enumerate()

    print (threadlist)

    sys.exit()



########################## ThreadedTCPRequestHandler #############
#
# 受信用ソケットスレッド制御クラス
#
##################################################################

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        data = self.request.recv(1024).strip()
        
        descriminate_recievedata(data,self.request)

        #cur_thread = threading.currentThread()
        cur_thread = threading.current_thread()

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)

##################################################################
#
#  pigpioのデーモン初期化
#
##################################################################
def start_pigpio_daemon():
    # pigpiod デーモンが動作しているか確認
    try:
        pi = pigpio.pi()
        if not pi.connected:
            print("pigpioデーモンが動作していないため、起動します。")
            # デーモンを起動
            subprocess.run(["sudo", "pigpiod"], check=True)
            # 再度接続を試みる
            pi = pigpio.pi()
            if not pi.connected:
                raise RuntimeError("pigpioデーモンの起動に失敗しました。")
        else:
            print("pigpioデーモンは既に動作しています。")
        return pi
    except Exception as e:
        raise RuntimeError(f"pigpioデーモンの確認中にエラーが発生しました: {e}")


########################## MAIN #############################

if __name__ == "__main__":

        print (COMMANDRESPONSE)

# Initialize InportModule
        main()


###################################################################
#
#
#  2024.5.20
#	PI.GPIOからpigpioへと変更

