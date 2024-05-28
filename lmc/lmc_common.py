#!/usr/bin/env python3
# -*- coding: utf-8 -*-

###############################################################################
# LMC-01 RPI Tutorial Scripts on Linux-Python
# lmc_common.py : lmc control system common script
# Ver.0.4 2016/03/02
# Ver.0.5 2016/03/22
#
# (C) Kyowa System Co.,ltd.   Takafumi Shindo
###############################################################################


import datetime
import os
import subprocess
import sys
import xml.dom.minidom
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import logging
import logging.handlers
import shlex
import atexit 
import fcntl
import socket
import glob
import re
import os
#import ConfigParser
import configparser
import time
import filecmp
import shutil
import chardet
import spidev
import signal

QUIETCOMMAND = " >/dev/null"

Logger=None
#DEBUGMODE = False
DEBUGMODE = True

####################################################################################################
# open_PILFont
# path   : フォントファイルを指定　/usr/share/font フォルダを参照するか、フルパスで指定する。
# size   : フォントサイズを指定
# index  : ttcフォントで使用　規定値は0。Pフォントなどを使用する場合1を指定する。他にも異字体を使用する場合に活用
####################################################################################################
def open_PILFont(path,size,index):
    #フォント展開
    root, ext = os.path.splitext(path)

    if ext == ".ttf" or ext == ".TTF" or ext == ".ttc" or ext == ".TTC":
        if os.path.exists(path) == True:
            font = ImageFont.truetype(path, size,index)
        else:
            print ("correct FontFile is not Found.[", path ,"]")
            sys.exit()
    else:
        print ("correct FontFile is not TrueType Fonts. LMC support only TrueType Fonts.[",path,u"]")
        sys.exit()
        
    return font


####################################################################################################
# error_cb
# e:error型で、ファイル名、エラー番号、エラー内容を含む。
# エラーが出たときにメッセージを標準出力に発行する。スクリプトの動作は停止しない。
####################################################################################################
def error_cb (e):
  print ("Could not open ",e.filename,'" ', str(e.errno)," ",e.strerror)

####################################################################################################
# filescan
# topdir:string型 ファイルを検索したいディレクトリのトップディレクトリパス。
# destination:string型で、検索するフォントのファイル名を指定する。
# destinationで指定されたファイルを、topdirで指定されたディレクトリの内部から検索し、発見したファイルのパスを返す。
####################################################################################################

def scanfileold(topdir,destination):
  # destinationはasciiかutf-8であること
  # 帰り値はUTF-8かASCII
  # for DEBUG deactivated
  returnstr = None
  for root, dirs, files in os.walk (topdir,topdown=False, onerror=error_cb):
    for f in files:
      destination_utf8=destination.encode('utf-8')
      result=chardet.detect(f.encode('utf-8'))
      if (result['encoding']=='utf-8'):
         if f in destination_utf8:
            returnstr = os.path.join (root,f)
            #print ("DEBUG Scanned and joined file name 　(UTF8): " +returnstr)
            return returnstr
      elif (result['encoding']=='SHIFT_JIS'):
         decodedfile=f.decode('SHIFT_JIS')
         file_utf8=decodedfile.encode('utf-8')
         if file_utf8 in destination_utf8:
            returnstr = os.path.join (root,file_utf8)
            #print ("DEBUG Scanned and joined file name 　(sjis): " +returnstr)
            return returnstr
      else :
         if f in destination:
            returnstr = os.path.join (root,f)
            return returnstr

  return ""


def scanfile(topdir,destination):
  # destinationはasciiかutf-8であること
  # 帰り値はUTF-8かASCII
  #print ("DEBUG Scan file start "+destination+ " from " +topdir)
  returnstr = None
  for root, dirs, files in os.walk (topdir,topdown=False, onerror=error_cb):
    for f in files:
         if f in destination:
            returnstr = os.path.join (root,f)
            return returnstr

  return ""

####################################################################################################
# findfont
# destination:string型で、検索するフォントのファイル名を指定する。
# destinationで指定されたtruetypeフォントファイルをフォントフォルダから検索し、発見したフォントのパスを返す。
####################################################################################################
def findfont(destination):
  result = ""
  result = scanfile("".join([os.environ.get("HOME"),"/.fonts/"]),destination)
  if result is None:
    result = scanfile("/usr/share/fonts/",destination)
  if result is None:
    result = scanfile("/usr/local/share/fonts/",destination)

  return result

####################################################################################################
# findimage   20151222
# destination:string型で、検索するイメージのファイル名を指定する。
# localimagefolder:定義ファイルで与えられるローカルイメージフォルダ /home/pi/lmc/image/ を想定
# tmpfolder:ramドライブを含む一次フォルダ
# destinationで指定されたイメージファイルをテンポラリフォルダ、ローカルイメージフォルダから検索し、発見したファイルのパスを返す。
####################################################################################################
def findimage(destination,localimagefolder):
  result = scanfile(localimagefolder,destination)

  return result

def SearchImageFile(lmcsconfig,File):
  if os.path.isabs(File):
     return File

  result=findimage(File,lmcsconfig.get_TempImagePath())
  if (result!=""):
     return result
  result=findimage(File,lmcsconfig.get_USBImagePath())
  if (result!=""):
     return result
  result=findimage(File,lmcsconfig.get_FTPRoot())
  if (result!=""):
     return result
  result=findimage(File,lmcsconfig.get_LocalImagePath())
  if (result!=""):
     return result

  return ""

def SearchPatternFile(lmcsconfig,File):
  if os.path.isabs(File):
     return File

  result=findimage(File,lmcsconfig.get_USBImagePath())
  if (result!=""):
     return result
  result=findimage(File,lmcsconfig.get_FTPRoot())
  if (result!=""):
     return result
  result=findimage(File,lmcsconfig.get_PatternPath())
  if (result!=""):
     return result

  return ""


def SearchGeneralFile(lmcsconfig,File):
  if os.path.isabs(File):
     return File

  result=findimage(File,lmcsconfig.get_FTPRoot())
  if (result!=""):
     return result
  result=findimage(File,lmcsconfig.get_PatternPath())
  if (result!=""):
     return result
  result=findimage(File,lmcsconfig.get_LocalImagePath())
  if (result!=""):
     return result

  return ""

########################## getfilelist #############################
# 指定したフォルダに内包されるファイルのリストを返す
# destinationで与えられた配列に追加する
###############################################################################

def getfilelistold(path,destination):

   res = glob.glob(path+'/*')

   if isinstance(res, list):
      for f in res:
        f=f.encode()
        result=chardet.detect(f)
        if (result['encoding']=='utf-8'):
           destination.append(f)
        elif (result['encoding']=='SHIFT_JIS'):
           decodedfile=f.decode('SHIFT_JIS')
           file_utf8=decodedfile.encode('utf-8')
           destination.append(file_utf8)
        else :
           destination.append(f)

   return destination


def getfilelist(path,destination):

   res = glob.glob(path+'/*')

   if isinstance(res, list):
      for f in res:
          destination.append(f)

   return destination


####################################################################################################
# getpasttime
# start  : datetime型 datetime.new() で取得したものを与えることを想定する
# caption: String型   経過時間の表題
# start で与えられた初期時間からの経過時間をミリ秒で表示する。
####################################################################################################
def getpasttime(start,caption):
    d2 = datetime.datetime.now()
    dt = d2-start
    result = dt.seconds + float(dt.microseconds)/1000000
    if caption != "":
        print ("[",caption,"] past time is ",str(result)," sec.")
    
    return result


####################################################################################################
# createDirectory
# 途中のディレクトリを含め、指定したパスのディレクトリを作成する。
####################################################################################################
def createDirectory(path):

    result = ""
    if os.path.exists(path) == False:
        splitPath = path.split("/")
        makedir = []
        for dir in splitPath:
            makedir.append(dir)
            destFolder = "/".join(makedir)
            if destFolder != "":
                if os.path.exists(destFolder) == False:
                    try:
                        os.mkdir(destFolder)
                    except IOError as ex:
                        result =  ex

                SetWritePermission(destFolder)
                result =" ".join(["Create Directory:",destFolder,"Successful."])
                print (result)
    return result


####################################################################################################
# SetWritePermission
# 指定したパスのパーミッションを書き込み可能にする。
####################################################################################################
def SetWritePermission(path):
    os.system("".join(["sudo chmod -R o+w ",path]))

###############################################################################
# detect_xmltemplate
# LMC用XMLLEDタイルテンプレートファイルの解析
# テンプレートが示す画面サイズの(x,y,w,h,tilecount)タプルを返す。
# インデックスを指定した場合、指定した領域のみの領域を返す
###############################################################################
def detect_xmltemplate(path,arguments):

    index = 0
    temptilelocation_x = 99999
    temptilelocation_y = 99999
    temptilelocation_w = 0
    temptilelocation_h = 0

    if arguments is not None:
        arguments = []
        split = arguments.split(' ')
        if Len(split) == 1:
            args.append(split)
        
        for arg in args:
            if r"index=" in arg:
                index = int(arg.replace(r"index=",""))
            #他の引数は未設定
    try :   
      dom = xml.dom.minidom.parse(path)
      for versionnode in dom.getElementsByTagName("VERSION"):
        version = int(versionnode.firstChild.data)

      if version == 4:
        #Version4解析モード
        tile_x = 0
        tile_y = 0
        tile_w = 0
        tile_h = 0
        tilecount=0

        for tilenode in dom.getElementsByTagName("TILE"):
            direction=0
            tilecount=tilecount+1
            for tileParameterNode in tilenode.childNodes:
                if tileParameterNode.nodeType == tileParameterNode.ELEMENT_NODE:
                    if tileParameterNode.tagName == "TileLocation_X":
                        tile_x =int(tileParameterNode.firstChild.data)
                    elif tileParameterNode.tagName == "TileLocation_Y":
                        tile_y =int(tileParameterNode.firstChild.data)
                    elif tileParameterNode.tagName == "TileLocation_W":
                        tile_w =int(tileParameterNode.firstChild.data)
                    elif tileParameterNode.tagName == "TileLocation_H":
                        tile_h =int(tileParameterNode.firstChild.data)
                    elif tileParameterNode.tagName == "TileDirection":
                        direction=int(tileParameterNode.firstChild.data)

            IfSwap=False
            if (direction==3):
                IfSwap=True
            elif (direction==4):
                IfSwap=True
            elif (direction==90):
                IfSwap=True
            elif (direction==270):
                IfSwap=True
            if (IfSwap):
               Swap=tile_w
               tile_w=tile_h
               tile_h=Swap

            if tile_x < temptilelocation_x:
                temptilelocation_x = tile_x
            if tile_y < temptilelocation_y:
                temptilelocation_y = tile_y
            if tile_x + tile_w > temptilelocation_w:
                temptilelocation_w = tile_x + tile_w
            if tile_y + tile_h > temptilelocation_h:
                temptilelocation_h = tile_y + tile_h

        for tilenode in dom.getElementsByTagName("BLOCK"):
            direction=0
            tilecount=tilecount+1
            for tileParameterNode in tilenode.childNodes:
                if tileParameterNode.nodeType == tileParameterNode.ELEMENT_NODE:
                    if tileParameterNode.tagName == "BlockLocation_X":
                        tile_x =int(tileParameterNode.firstChild.data)
                    elif tileParameterNode.tagName == "BlockLocation_Y":
                        tile_y =int(tileParameterNode.firstChild.data)
                    elif tileParameterNode.tagName == "BlockLocation_W":
                        tile_w =int(tileParameterNode.firstChild.data)
                    elif tileParameterNode.tagName == "BlockLocation_H":
                        tile_h =int(tileParameterNode.firstChild.data)
                    elif tileParameterNode.tagName == "BlockDirection":
                        direction=int(tileParameterNode.firstChild.data)
            IfSwap=False
            if (direction==3):
                IfSwap=True
            elif (direction==4):
                IfSwap=True
            elif (direction==90):
                IfSwap=True
            elif (direction==270):
                IfSwap=True
            if (IfSwap):
               Swap=tile_w
               tile_w=tile_h
               tile_h=Swap
            if tile_x < temptilelocation_x:
                temptilelocation_x = tile_x
            if tile_y < temptilelocation_y:
                temptilelocation_y = tile_y
            if tile_x + tile_w > temptilelocation_w:
                temptilelocation_w = tile_x + tile_w
            if tile_y + tile_h > temptilelocation_h:
                temptilelocation_h = tile_y + tile_h


      #tilecount = (int(temptilelocation_w - temptilelocation_x) /8) * (int(temptilelocation_h - temptilelocation_y) /8)

      result = (temptilelocation_x,temptilelocation_y,temptilelocation_w,temptilelocation_h,tilecount)

      print ("TileTemplate:", path ,u"Version" ,str(version),str(result),u"loaded.")
    except Exception as e:
      print (f" XML error detected. {e}")
      return None

    return result


def Log(source,logger):

    if (logger==None):
        return
    td = datetime.datetime.now()
    st = ":".join([str(td.hour).zfill(2),str(td.minute).zfill(2),str(td.second).zfill(2)])
    logger.debug(">>>".join([st,source]))
    
########################## ifconfig #############################
# 指定したインターフェイスに割り当てられているIPアドレスを文字列で返す。
# 基本はeth0で、複数のインターフェイスがあった場合、それぞれについてこのメソッドを呼び出す。
###############################################################################
def ifconfig(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        result = fcntl.ioctl(s.fileno(), 0x8915 ,(ifname+'\0'*32)[:32])
    except IOError:
        return None

    return socket.inet_ntoa(result[20:24])



###################### ScriptConfig ################################
# 各スクリプトで使用する設定ファイルの基本管理クラス
# 
# 
####################################################################
class ScriptConfig(object):
    def __init__(self):

        self.lmcHomePath = os.path.abspath(os.path.dirname(__file__))   #絶対ディレクトリの取得　lmcフォルダになる
        sys.path.append(self.lmcHomePath)                                                               #スクリプトのルートにパスを通す

        self.configLoad()

        #作業フォルダ作成
        createDirectory(self.tmpPath)
        createDirectory(self.get_TempWorkPath())
        createDirectory(self.get_TempImagePath())


    def configLoad(self):

        self._ConfigFileName = os.path.join(self.lmcHomePath,"LMCRPIT_config.ini")

        self._SystemConfigTag = "System"
        self._BaseConfigTag = "LEDControl"
        self._LMCServerConfigTag = "LMCServer"
        self._FTPServerConfigTag = "FTPServer"
        self._HTTPServerConfigTag ="HTTPServer"
        self._LMCSlaveConfigTag ="LMCSlave"
        self._LMCThruConfigTag ="LMCThru"
        self._SchedulerConfigTag ="LMCScheduler"

        self.IfMaster=False
        self.LMCType="LMC"
        self.USBPath="/mnt/usb1/"
        self.USBUpdator="/mnt/usb1/lmc/"
        self.WIFIControl=False
        self.APMODE = "AP"
        self.AP_SSID = "lmcwlan"
        self.AP_KEY = "12345678"
        self.AP_IP = "10.0.0.120"
        self.AP_HW_MODE="g"
        self.AP_WPA_KEY_MGMT="WPA-PSK"
        self.AP_WPA_PAIRWISE="TKIP"
        self.AP_RSN_PAIRWISE="CCMP"
        self.WIFI_SSID ="userwifi"
        self.WIFI_KEY = "userpassword"
        self.INIT_SSID = 'lmcinit'
        self.AP_INIT = "INIT"
        self.POWERMODE = "WLAN"
        self.CPUFREQHMZ=""
        self.SPIFREQRATIO=1.0
        self.SystemGroup="LMCPanel"
        self.IfSilentBoot=False
        self.ftpEnabled = True
        self.ApplicationName="LEDMultiControl"

        self.pidDir = "pid"
        self.pidName = "lmcctl.pid"

        self.localImagePath="image"
        self.ftpDir="user/"
        self.tmpPath="/var/tmp/lmc/"
        self.patternPath="pattern/"
        self.patternFile="FC_64x32.dat"
        self.multiPatternFile=""
        self.localImagePath="image"
        self.ledControllPath="LEDMultiControl/LEDMultiControl"
        self.ledMultiControllPath="LEDMultiControl/LEDMultiControl"
        self.brightnesslimit=24
        self.brightness=255
        self.highcurrentmode=False
        self.framelatencymulti=2
        self.logDirectory="log"
        self.logFileName="lmcs_command.log"
        self.commandPort =10020
        self.MultiConfigFile="LMCMultiConfig.json"
        self.slavecontrol="LEDMultiControl/LEDMultiControl"
        self.SlaveID=0
        self.slaveconfigfilename="LMCConfig.json"

        self.IfSlaveEnabled=False
        self.IfSlaveCommandServer=False
        self.SlaveCommandPort=10021
        self.slavepatternfile="FC_64x32.dat"
        self.schedulerFilePath = ""
        self.schedulerPath=""

        self._CommonOptions=[]

        config = configparser.ConfigParser()
        config.read(self._ConfigFileName)
        try:
                print("System section")
                if config.has_option(self._SystemConfigTag,'lmctype'):
                   self.LMCType=config.get(self._SystemConfigTag,'lmctype')
                if (config.get(self._SystemConfigTag,'MASTER')=='true'):
                   self.IfMaster=True
                self.USBPath=config.get(self._SystemConfigTag,'USB_PATH')
                self.USBUpdator=config.get(self._SystemConfigTag,'USB_UPDATOR')
                if (config.get(self._SystemConfigTag,'WIFICONTROL')=='true'):
                   self.WIFIControl=True
                self.APMODE = config.get(self._SystemConfigTag,'APMODE')
                self.AP_SSID = config.get(self._SystemConfigTag,'AP_SSID')
                self.AP_KEY = config.get(self._SystemConfigTag,'AP_KEY')
                self.AP_IP = config.get(self._SystemConfigTag,'AP_IP')
                self.AP_HW_MODE=config.get(self._SystemConfigTag,'AP_HW_MODE')
                self.AP_WPA_KEY_MGMT=config.get(self._SystemConfigTag,'AP_WPA_KEY_MGMT')
                self.AP_WPA_PAIRWISE=config.get(self._SystemConfigTag,'AP_WPA_PAIRWISE')
                self.AP_RSN_PAIRWISE=config.get(self._SystemConfigTag,'AP_RSN_PAIRWISE')
                self.WIFI_SSID = config.get(self._SystemConfigTag,'WIFI_SSID')
                self.WIFI_KEY = config.get(self._SystemConfigTag,'WIFI_KEY')
                self.INIT_SSID = u'lmcinit'
                self.AP_INIT = config.get(self._SystemConfigTag,'AP_INIT')
                self.POWERMODE = config.get(self._SystemConfigTag,'POWERMODE')
                self.CPUFREQMHZ = config.get(self._SystemConfigTag,'CPUFREQMHZ')
                self.SPIFREQRATIO = config.get(self._SystemConfigTag,'SPIFREQRATIO')
                self.SystemGroup=config.get(self._SystemConfigTag,'GROUP')
                if (config.get(self._SystemConfigTag,'silentboot')=='true'):
                   self.IfSilentBoot=True
                if config.has_option(self._SystemConfigTag,'APPLICATIONNAME'):
                   self.ApplicationName = config.get(self._SystemConfigTag,'APPLICATIONNAME')
                print("LEDControl section")

                self.pidDir = config.get(self._BaseConfigTag,'pid_dir')
                self.pidName = config.get(self._BaseConfigTag,'pid_name')
                
                self.pidName_LC = config.get(self._LMCServerConfigTag,'pid_name')

                self.ftpEnabled = config.get(self._FTPServerConfigTag,'ftp_enabled')
                self.pidName_FTP = config.get(self._FTPServerConfigTag,'pid_name')
                self.pidName_Slave = config.get(self._LMCSlaveConfigTag,'pid_name')
                self.pidName_Thru = config.get(self._LMCThruConfigTag,'pid_name')
                self.pidName_Scheduler = config.get(self._SchedulerConfigTag,'pid_name')


                self.ftpDir = os.path.join(config.get(self._BaseConfigTag,'ftp_dir'))
                self.tmpPath = os.path.join(config.get(self._BaseConfigTag,'tmp_path'))
                
                self.patternPath = os.path.join(self.lmcHomePath,config.get(self._BaseConfigTag,'patternpath'))


                print("LEDControl section 2")

                self.patternFile = config.get(self._BaseConfigTag,'defaultpatternfile')
                self.multiPatternFile = config.get(self._BaseConfigTag,'defaultmultipatternfile')
                self.localImagePath = config.get(self._BaseConfigTag,'localimagepath')

                self.brightnesslimit=config.get(self._BaseConfigTag,'brightnesslimit')
                self.brightness=config.get(self._BaseConfigTag,'brightness')
                if config.has_option(self._BaseConfigTag,'highcurrentmode'):
                   if (config.get(self._BaseConfigTag,'highcurrentmode')=='true'):
                       self.highcurrentmode = True

                self.framelatencymulti=config.get(self._BaseConfigTag,'framelatencymulti')
                self.logDirectory = config.get(self._BaseConfigTag,'logdirectory')
                self.logFileName = config.get(self._BaseConfigTag,'logfilename')
                print("LMCServer section")

                self.ledControllPath = os.path.realpath(os.path.join(self.lmcHomePath,config.get(self._LMCServerConfigTag,'ledcontrollocation')))
                self.ledMultiControllPath = os.path.realpath(os.path.join(self.lmcHomePath,config.get(self._LMCServerConfigTag,'ledcontrollocation')))

                self.commandPort = config.get(self._LMCServerConfigTag,"commandport")
                self.MultiConfigFile = config.get(self._LMCServerConfigTag,"multiconfigfile")

                print("LMCSlave section")

                if (config.get(self._LMCSlaveConfigTag,'ifslaveenabled')=='true'):
                   self.IfSlaveEnabled=True
                #if (config.get(self._LMCSlaveConfigTag,'ifslavecommandserver')=='true'): 
                #   self.IfSlaveCommandServer=True
                #self.SlaveCommandPort=config.get(self._LMCSlaveConfigTag,'slavecommandport')
                self.slavecontrol = config.get(self._LMCSlaveConfigTag,'slavecontrol')
                self.slavepatternfile = config.get(self._LMCSlaveConfigTag,'patternfile')
                self.slavepid_name = config.get(self._LMCSlaveConfigTag,'pid_name')
                self.slaveconfigfilename=config.get(self._LMCSlaveConfigTag,'configfile')
                self.SlaveID=config.get(self._LMCSlaveConfigTag,'slaveid')

                print("LMCThru section")

                self.thrucontrol = config.get(self._LMCThruConfigTag,'thrucontrol')
                self.thrupid_name = config.get(self._LMCThruConfigTag,'pid_name')
                self.thrutcpport = config.get(self._LMCThruConfigTag,'tcpport')
                self.thruudpport = config.get(self._LMCThruConfigTag,'udpport')

                print("Scheduler section")

                self.schedulerFilePath = config.get(self._SchedulerConfigTag,'scheduler_filename')
                self.schedulerPath = config.get(self._SchedulerConfigTag,'scheduler_name')
        except configparser.NoSectionError as e:
                print (f"No section error: {e}")
        except configparser.NoOptionError as e:
                print (f"No option error: {e}")

        del config
        self.config=None

    def get_IfMasterMode(self):
        return self.IfMaster

    def get_IfSlaveEnabled(self):
        return self.IfSlaveEnabled

    def get_brightnesslimit(self):
        return self_brightnesslimit

    def get_brightness(self):
        return self_brightness
 
    def get_SlaveID(self):
        return self.SlaveID

   
    #
    #  Filepath section
    #
    def get_LMCHomePath(self):
        return self.lmcHomePath

    def get_TempImagePath(self):
        return os.path.join(self.tmpPath,self.localImagePath)

    def get_LocalImagePath(self):
        return os.path.join(self.lmcHomePath,self.localImagePath)

    def get_USBImagePath(self):
        return os.path.join(self.USBPath)

    def get_TempWorkPath(self):
        return os.path.join(self.tmpPath,"work")

    def get_LEDControlPath(self):
        return os.path.join(self.lmcHomePath,self.ledControllPath)

    def get_LEDMultiControlPath(self):
        return os.path.join(self.lmcHomePath,self.ledMultiControllPath)

    def get_MultiConfigPath(self):
        return os.path.join(self.lmcHomePath,self.ftpDir,self.MultiConfigFile)

    def get_TemporaryMultiConfigPath(self):
        return os.path.join(self.tmpPath,self.MultiConfigFile)

    def get_TemporaryMultiConfigCompletedPath(self):
        MultiConfigCompletedFile=self.MultiConfigFile+".Completed"
        return os.path.join(self.tmpPath,MultiConfigCompletedFile)

    def get_MultiPatternPath(self):
        return os.path.join(self.lmcHomePath,self.patternPath,self.multiPatternFile)

    def get_SlavePatternPath(self):
        return os.path.join(self.lmcHomePath,self.patternPath,self.slavepatternfile)

    def get_TemporaryMultiPatternPath(self):
        return os.path.join(self.tmpPath,self.multiPatternFile)

    def get_FTPRoot(self):
        return os.path.join(self.lmcHomePath,self.ftpDir)

    def get_PatternPath(self):
        return os.path.join(self.patternPath)

    def get_PatternFile(self):
        return os.path.join(self.patternFile)
  
    def get_SchedulerPath(self):
        return os.path.join(self.lmcHomePath,self.schedulerPath)

    def get_SchedulerFilePath(self):
        return os.path.join(self.lmcHomePath,self.ftpDir,self.schedulerFilePath)
      
    def get_PIDRootPath(self):
        return os.path.join(self.tmpPath,self.pidDir)

    def get_PIDPath_LC(self):
        return os.path.join(self.get_PIDRootPath(),self.pidName_LC)

    def get_PIDPath(self):
        return os.path.join(self.get_PIDRootPath(),self.pidName)

    def get_PIDPath_FTP(self):
        return os.path.join(self.get_PIDRootPath(),self.pidName_FTP)

    def get_PIDPath_Slave(self):
        return os.path.join(self.get_PIDRootPath(),self.pidName_Slave)

    def get_PIDPath_Thru(self):
        return os.path.join(self.get_PIDRootPath(),self.pidName_Thru)

    def get_PIDPath_Scheduler(self):
        return os.path.join(self.get_PIDRootPath(),self.pidName_Scheduler)

#
#   Access to Config 
#
    def loadConfigFile(self):
       print (" Load config file")
       self.config = configparser.ConfigParser()
       self.config.read(self._ConfigFileName)
       return True
 
    def saveConfigFile(self):
       # Catch exception . TODO
       if (self.config==None):
           return False
       try:
          with open(self._ConfigFileName, 'w') as configfile:
             self.config.write(configfile)
          print (" Save config file")
          #Reload config
          self.configLoad()
       except EnvironmentError:
          print (" Failed to write config file")

       return True

    def getSpecifiedConfig(self,Section,Variable):
       if (self.config==None):
           self.loadConfigFile()
       if (self.config.has_option(Section, Variable)==False):
           print ("Error: Config variable [",Section,"] ",Variable," not found")
           return None
       return self.config.get(Section,Variable)

    def setSpecifiedConfig(self,Section,Variable,Value):
       if (self.config==None):
          self.loadConfigFile()
       if (self.config.has_section(Section)==False):
           #self.config.add_section(Section,Variable)
           print ("Error: Config section ",Section," not found")
           return False
       if (self.config.has_option(Section, Variable)==False):
           print ("Error: Config variable [",Section,"] ",Variable," not found")
           return False
       print ("Set Config " ,Variable,Value)
       self.config.set(Section,Variable,Value)
       return True

    def dumpConfigScripts(self):
       if (self.config==None):
           self.loadConfigFile()
       SectionList=self.config.sections()
       ResultList=[]
       print ( "Dump config files ",SectionList)
       for section in SectionList:
          print (" current section: ",section)
          currentsection=self.config.items(section)
          for key in currentsection:
              ResultString=section+"."+key[0]+"="+key[1]
              print (" ",ResultString)
              ResultList.append(ResultString)

       return ResultList

#
#    Common variables
#
    def get_LMCCommandCommonOptions(self):
        return self._CommonOptions

    def add_LMCCommandCommonOptions(self,AddValue):
        self._CommonOptions.append(AddValue)

########################### show_ImageMovieFile #########################
# show_ImageMovieFile(lmcsconfig,splitstr)
# ファイル上の動画をLEDパネルに表示 
# 引数： lmcsconfig 設定クラスインスタンス , 
#        splitstr   コマンド引数 要素[0]は必ずlmiファイルパスであること
###############################################################################
def show_ImageMovieFile(lmcsc,splitstr):

        print ("start show_ImageMovieFile")
        
        ifMasterMode = False
        xpos=0
        ypos=0
        IfHorizontalScroll=False
        IfVerticalScroll=False


        filename=""
  
        num = len(splitstr)

        sPidPath = u"-P"+lmcsc.get_PIDPath()
 
        OtherOptions=[]
        OtherOptions.extend(lmcsc._CommonOptions)

        currentMultiPatternPath=""
        if (lmcsc.multiPatternFile!=""):
            currentMultiPatternPath=GetSpecifiedMultiPatternFile(lmcsc,lmcsc.multiPatternFile)

        currentPatternPath=""
        if (lmcsc.patternFile!=""):
            currentPatternPath=SearchPatternFromFile(lmcsc,lmcsc.patternFile)

        print ("Default TileTemplateFile: "+currentPatternPath)
        print ("Default MultiTileTemplateFile: "+currentMultiPatternPath)

        for arg in splitstr:
            if arg.startswith("-T"):
                #パターン指定 検索、アサイン無し
                tmpPatternPath = arg.replace('-T',"")
                print ("Specified single template " + tmpPatternPath)
 
                currentPatternPath=SearchPatternFromFile(lmcsc,tmpPatternPath)

            elif arg.startswith("-t"):
                #マルチパターン指定
                tmpMultiPatternPath = arg.replace('-t',"")
                print ("Specified multi template " +tmpMultiPatternPath)

                ResultPath=GetSpecifiedMultiPatternFile(lmcsc,tmpMultiPatternPath)
                if (ResultPath!=None):
                    currentMultiPatternPath=ResultPath
            elif arg=="-sc" :
                IfHorizontalScroll = True
                OtherOptions.append(arg)
            elif arg=="-sv":
                IfVerticalScroll = True
                OtherOptions.append(arg)
            elif arg.startswith("-PX"):
                #座標指定があった場合 X
                xpos = int(arg.replace('-PX',""))  
            elif arg.startswith("-PY"):
                #座標指定があった場合 Y
                ypos = int(arg.replace('-PY',""))  

            elif arg.startswith("-m"):
                print ("DEBUG : Master mode")
                if len(arg) == 2:
                     ifMasterMode=True
                else:
                     OtherOptions.append(arg)
                     print ("Other options "+arg)
            elif arg.startswith("--"):
                #LEDMultiControlに送らない
                continue
            elif arg.startswith("-"):
                OtherOptions.append(arg)
                print ("Other options "+arg)
            else:
                filename = arg
                filename = filename.replace("\r","")
                filename = filename.replace("\n","")
                filename = SearchImageFile(lmcsc,filename)
                #print ("Found animation filename " +filename)

        print ("animation filename :" +filename)
        if currentPatternPath == "":
            print ("Error! ","TilePatternFile was not selected in options.")
            return False

        LEDControlPath = lmcsc.get_LEDControlPath()

        if ifMasterMode:
            if (currentMultiPatternPath!=""):
                spiLayout_multiControlPatternOption = "".join(["-t",currentMultiPatternPath])
                #SlaveとなるLEDBlockの配置を示す。
            else:
                spiLayout_multiControlPatternOption = "".join(["-t",currentPatternPath])
            OtherOptions.append("-m")
        else:
            spiLayout_multiControlPatternOption = "".join(["-p",currentPatternPath])
            #SPI系統に接続されているLEDタイルの配置を示す。単独動作では-bと同一のファイルを指定

        if IfHorizontalScroll :
           if ypos!=0:
                OtherOptions.append("-so"+str(ypos))
        if IfVerticalScroll :
           if xpos!=0:
                OtherOptions.append("-so"+str(xpos))

        if filename is None :
           FinalCommand=[u"sudo",LEDControlPath,spiLayout_multiControlPatternOption,sPidPath]
        else:
           FilenameInQuote="'"+filename+"'"
           FinalCommand=[u"sudo",u"nice",u"-n",u"-10",LEDControlPath,spiLayout_multiControlPatternOption,filename,sPidPath]
        FinalCommand.extend(OtherOptions)

        print ("FinalCommand : ")
        print (FinalCommand)
        sendCommand = " ".join(FinalCommand)

        #PIDファイルが存在したら前のプロセス強制消去
        # Killが完全に終わってから、次のプロセスを開始する必要がある。注意。
        stop_ProcessfromPID(lmcsc.get_PIDPath())
        WaitUntilLMCEnds(lmcsc,3)


        createdsubprocess=subprocess.Popen(FinalCommand, shell=False)
        #createdsubprocess.wait()
        outs, errs = createdsubprocess.communicate()

        #print ("DEBUG: Result output " , outs,",",errs)
        destinationPID=lmcsc.get_PIDPath()
        if os.path.exists(destinationPID) == True:
           # Normal end
           print ("LMC process normal end")

           RemoveProcessfromPID(destinationPID)
           return True
        else:
           # Already aborted
           print ("LMC process was aborted")
           return False
##
##
##

########################### Slave server #########################
#   SlaveServerを起動
###############################################################################


def CreateAssignedMultiPattern(lmcsc,MultiPatternName):
    # JSONファイルのIP,ID対応表に従い、MultiPatternNameのXMLを改変して出力する 
    global Logger
    if (MultiPatternName==""):
        return ""

    TemporaryMultiConfigPath=lmcsc.get_TemporaryMultiConfigPath()
    TargetMultiPatternPath=os.path.join(lmcsc.tmpPath,MultiPatternName)
    UserMultiPatternPath=os.path.join(lmcsc.get_FTPRoot(),MultiPatternName)
    TemporaryMultiConfigCompletedPath=lmcsc.get_TemporaryMultiConfigCompletedPath()
    Log("CreateAssignedMultiPattern()",Logger)

    OriginalPatternPath=os.path.join(lmcsc.get_PatternPath(),MultiPatternName)
    if not os.path.exists(OriginalPatternPath):
         return UserMultiPatternPath

    print ("Original pattern path :",OriginalPatternPath)
    print ("Target template File : ",TargetMultiPatternPath)

    ScanCurrentSlaves(lmcsc)
    if not os.path.exists(TemporaryMultiConfigPath):
       Log(u"".join([u"Slave scan failed. Use original pattern",""]),Logger)
       return OriginalPatternPath

    Log("Start to create XML File from IP config file",Logger)
    print ("Start to create XML File from IP config file.")
    print ("Using template File : ",OriginalPatternPath)

    SlaveIsAllReady=subprocess.call(["sudo","python3","lmcJSONtoXML.py",TemporaryMultiConfigPath,OriginalPatternPath,TargetMultiPatternPath], shell=False)

    if (SlaveIsAllReady==0):
        Log("Slave is all ready. Setup temporary pattern file",Logger)
        # tmpフォルダにTouch 
        with open(TemporaryMultiConfigCompletedPath, "w") as f:
            pass
    if os.path.exists(TargetMultiPatternPath):
               # Userフォルダにコピーを行う。
               # UserフォルダのPatternファイルと比較して、不一致ならば上書きする。
               print ("User temporary template File : ",UserMultiPatternPath)

               if not os.path.exists(UserMultiPatternPath):
                   print ("Update user template file")
                   shutil.copy(TargetMultiPatternPath,UserMultiPatternPath)
               elif (not filecmp.cmp(TargetMultiPatternPath, UserMultiPatternPath,False)):
                   print ("Update user template file")
                   shutil.copy(TargetMultiPatternPath,UserMultiPatternPath)
               # Userフォルダ内部へのパスを返す 
               return UserMultiPatternPath
    else:
       return ""


def ScanCurrentSlaves(lmcsc):
    global Logger
    Log("ScanCurrentSlaves()",Logger)
    #print "DEBUG: ScanCurrentSlaves()"
    # SlaveのIPを検索して、Configファイルを作成する。
    TemporaryMultiConfigPath=lmcsc.get_TemporaryMultiConfigPath()

    # Network上のSlaveをスキャンして、JSONファイルを生成する。 

    createdsubprocess=subprocess.Popen(["sudo","python3","lmclanscantoJSON.py",TemporaryMultiConfigPath], shell=False)
    createdsubprocess.wait()

    if not os.path.exists(TemporaryMultiConfigPath):
        Log("Config pattern is not ready",Logger)
        return

    UserTempConfigPath=lmcsc.get_MultiConfigPath()

    if not os.path.exists(UserTempConfigPath):
        print ("Update user slave configuration file")
        shutil.copy(TemporaryMultiConfigPath,UserTempConfigPath)
    elif (not filecmp.cmp(TemporaryMultiConfigPath, UserTempConfigPath,False)):
        print ("Update user slave configuration file")
        shutil.copy(TemporaryMultiConfigPath,UserTempConfigPath)


########################## search specified pattern from file system  #############################
# パターンをファイルシステムから検索する。
# 引数：currentPatternPath デフォルトパス tmpPatternPath 指定されたパターン。パス部分なし
# 戻り値：発見されたパターンのフルパス
#################################################################################

#
#  指定されたパターンを検索する。パターンはSlaveアサインされない。
#
def SearchPatternFromFile(lmcsc,PatternName):

    print ("Searching pattern name " , PatternName)
    FoundPatternPath = PatternName
    if os.path.isabs(PatternName) == False:
                print ("Scan from FTPRoot")
                # FTPRoot==UserPathから検索  
                result = scanfile(lmcsc.get_FTPRoot(),PatternName)

                if result !="":
                    FoundPatternPath = os.path.join(lmcsc.get_FTPRoot(),PatternName)
                else:
                    # PatternPathから検索  
                    print ("Scan from Patternpath ")
                    result = scanfile(lmcsc.get_PatternPath(),PatternName)

                    if result !="":
                        FoundPatternPath = os.path.join(lmcsc.get_PatternPath(),PatternName)

                if os.path.isfile(PatternName):
                    currentPatternPath = tmpPatternPath
                    print (" Found TemplateFile : ",FoundPatternPath )

    print ("Use specified pattern path " + FoundPatternPath)
    return FoundPatternPath

#
#  Slaveアサインされたパターンを取得する。必要であればその都度Slaveアサインを行う。
#
def GetSpecifiedMultiPatternFile(lmcsc,PatternName):

     TemporaryMultiConfigPath=lmcsc.get_TemporaryMultiConfigPath()
     if os.path.exists(TemporaryMultiConfigPath):
        if os.path.exists(lmcsc.get_TemporaryMultiConfigCompletedPath()):
          # Configがすでに設定されている。既存のパターンがあるはずなので検索する
          UserTempPatternPath=os.path.join(lmcsc.tmpPath,PatternName)
          print ("GetSpecifiedMultiPatternFile : input pattern name : " , UserTempPatternPath)
          #対象ファイルを検索
          if os.path.isfile(UserTempPatternPath):
            return UserTempPatternPath

     print ("Reassign slaves: input pattern name : " , TemporaryMultiConfigPath)

     ResultPatternPath=CreateAssignedMultiPattern(lmcsc,PatternName)
  
     print ("Get specified multi pattern path " , ResultPatternPath)
     return ResultPatternPath

#
#  Reset config files .. Reassign slaves
#
def ResetMultiPatternFile(lmcsc):

     TemporaryMultiConfigPath=lmcsc.get_TemporaryMultiConfigPath()
     TemporaryMultiConfigCompletedPath=lmcsc.get_TemporaryMultiConfigCompletedPath()
     try:
        os.remove(TemporaryMultiConfigPath)
        os.remove(TemporaryMultiConfigCompletedPath)
     except OSError:
        pass
#
# ロガーの初期設定を行う。
# 引数：lmcsc ScriptConfig型設定クラスインスタンス name:記録を行うログの名称
# 戻り値：ロガークラスのインスタンス
#################################################################################
def initialize_logger(lmcsc,name):
    global Logger
    LOGDIR = os.path.join(lmcsc.tmpPath,lmcsc.logDirectory)

    createDirectory(LOGDIR)

    LOGFILENAME = os.path.join(LOGDIR,lmcsc.logFileName)
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    handler = logging.handlers.RotatingFileHandler(LOGFILENAME,maxBytes=65536,backupCount=256)
    logger.addHandler(handler)
    Logger=logger

    return logger

#
#  Separatorで分割する  quoteの内部は分割しないことに注意
#################################################################################


def CustomizedSplitSpace(InputLine,Separator,Separator2):
  #print ("DEBUG CustomizedSplitSpace input "+ InputLine);
  InsideQuotation=False
  InsideQuotation2=False
  ResultList=[]
  ResultListItem = ""
  for char in InputLine:
     if char=='\'':
       if InsideQuotation:
           InsideQuotation=False
       else:
           InsideQuotation=True
     if char=='"':
       if InsideQuotation2:
           InsideQuotation2=False
       else:
           InsideQuotation2=True

     if InsideQuotation==False:
        if InsideQuotation2==False:
           if (char==Separator) or (char==Separator2):
              if (ResultListItem != ""):
                 #print ("DEBUG CustomizedSplitSpace ResultListItem " +ResultListItem);
                 ResultList.append(ResultListItem)
                 ResultListItem=""
              continue
     ResultListItem+=char
     #print ("DEBUG CustomizedSplitSpace " , char);

  if (ResultListItem!=""):
     ResultList.append(ResultListItem)
  return ResultList

########################## getnum #############################
#  正規表現で引数から連続した数値のみを抽出する
#################################################################################
def getnum(source):

    p = re.compile(r'\d+')
    result = p.search(source)
    if result is None:
        return ""
    else:
        return result.group()



########################## StopProcessfromPID ###################
# 指定したPIDのプロセスに終了Signalを送って停止させる
##################################################################
def stop_ProcessfromPID(destinationPID,IfNetworking=False):
    #kill_ProcessfromPID(destinationPID)
    #return

    if os.path.exists(destinationPID) == True:
        try:
           f = open(destinationPID,"r")
           rstr = f.read()
           os.remove(destinationPID)
           f.close()
        except OSError:
           pass
        # Linux only. Not works on Windows
        print("Send break to sub process ",destinationPID," ",rstr)
        try:
            if (IfNetworking):
                retcode=os.kill(int(rstr), signal.SIGTERM)
            else:
                retcode=os.kill(int(rstr), signal.SIGINT)
        except OSError as e:
           print (" process break signal failed.")
        print("Stopped ",destinationPID," ",rstr)
        # Wait time
        time.sleep(0.2)
    else:
        print (" No working LMC process : ",destinationPID)
    

########################## kill_ProcessfromPID ###################
# 指定したPIDのプロセスを終了する
##################################################################
def kill_ProcessfromPID(destinationPID):

    if os.path.exists(destinationPID) == True:
        try:
           f = open(destinationPID,"r")
           rstr = f.read()
           os.remove(destinationPID)
           f.close()
        except OSError:
           pass

#        subprocess.call('sudo kill -s 9 ' + rstr,shell=False)
#        subprocess.call('sudo kill -SIGINT ' + rstr,shell=False)
#        subprocess.call('bash ./killtree.bash ' + rstr ,shell=False)
        print("Try to kill ",destinationPID," ",rstr)
        try:
           retcode=subprocess.check_call(["python3","killtree.py",rstr] ,shell=False)
        except subprocess.CalledProcessError as e:
           print (" Process kill failed.")
        print("Killed ",destinationPID," ",rstr)
        # Wait time
        time.sleep(0.2)
    else:
        print (" No working LMC process : ",destinationPID)


def RemoveProcessfromPID(destinationPID):
    if os.path.exists(destinationPID) == True:
        os.remove(destinationPID)



########################## killall_ProcessfromName ###################
# 指定したパスのプロセスを全て終了する
##################################################################
def killall_ProcessfromName(ProcessPathName):
    
    processname=os.path.basename(ProcessPathName)
    try:
      retcode=subprocess.check_call(['killall',processname],shell=False)
    except subprocess.CalledProcessError as e:
      print (" Process kill failed.")


##################################################################
# LMCの動作終了待ち
##################################################################
def CheckLMCisStillRunning(lmcsc):
    appname=lmcsc.ApplicationName
    try:
       FoundLMCs=False
       Result=subprocess.check_output("ps aux | grep "+appname,shell=True)
       Result=Result.decode()
       ResultLines=Result.split('\n')
       for ResultLine in ResultLines:
          FoundLMC=False
          WorkingOptions=ResultLine.split(' ')
          for WorkingCommand in WorkingOptions:
             if (WorkingCommand=='-s'):
                FoundLMC=False
                continue
             Place=WorkingCommand.rfind(appname)
             if (Place<0):
                # Not match
                continue
             if (Place==0):
                # No path -> NOT command
                continue
             else:
                FoundLMC=True
                #print("DEBUG :ResultLine ",ResultLine)
          if FoundLMC:
              FoundLMCs=True
  
    except subprocess.CalledProcessError as e:
       print (" Subprocess error ignored.")

    return FoundLMCs

def CheckLMCSlaveisStillRunning(lmcsc):

    appname=lmcsc.ApplicationName
    try:
       FoundLMCs=False
       Result=subprocess.check_output("ps aux | grep "+appname,shell=True)
       Result=Result.decode()
       ResultLines=Result.split('\n')
       for ResultLine in ResultLines:
          FoundLMC=False
          FoundLMCSlave=False
          WorkingOptions=ResultLine.split(' ')
          for WorkingCommand in WorkingOptions:
             if (WorkingCommand=='-s'):
                FoundLMCSlave=True
                continue
             Place=WorkingCommand.rfind(appname)
             if (Place<0):
                # Not match
                continue
             if (Place==0):
                # No path -> NOT command
                continue
             else:
                FoundLMC=True
          if FoundLMC and FoundLMCSlave:
              FoundLMCs=True
  
    except subprocess.CalledProcessError as e:
       print (" Subprocess error ignored.")


    return FoundLMCs

def CheckSchedulerisStillRunning():
    appname="scheduler.py"
    try:
       FoundScheduler=False
       Result=subprocess.check_output("ps aux | grep "+appname,shell=True)
       Result=Result.decode()
       ResultLines=Result.split('\n')
       for ResultLine in ResultLines:
          WorkingOptions=ResultLine.split(' ')
          for WorkingCommand in WorkingOptions:
             Place=WorkingCommand.rfind(appname)
             if (Place<0):
                # Not match
                continue
             if (Place==0):
                # No path -> NOT command
                continue
             else:
                FoundScheduler=True
                print  ("Scheduler is still running : ",ResultLine)
 
    except subprocess.CalledProcessError as e:
       print (" Subprocess error ignored.")


    return FoundScheduler

def WaitUntilLMCEnds(lmcsc,WaitSeconds):
    WaitCount=WaitSeconds*10
    i=0
    for i in range(1,WaitCount):
        if not CheckLMCisStillRunning(lmcsc):
            break
        time.sleep(0.1)

def WaitUntilLMCSlaveEnds(lmcsc,WaitSeconds):
    WaitCount=WaitSeconds*10
    i=0
    for i in range(1,WaitCount):
        if not CheckLMCSlaveisStillRunning(lmcsc):
            break
        time.sleep(0.1)


def WaitUntilSchedulerEnds(WaitSeconds):
    WaitCount=WaitSeconds*10
    i=0
    for i in range(1,WaitCount):
        if not CheckSchedulerisStillRunning():
            break
        time.sleep(0.1)

def GetDiskFreespace():
    try: 
      fd = os.open( "lmc_common.py", os.O_RDONLY )
      info = os.fstatvfs(fd)
      return info.f_bfree*info.f_bsize
    except OSError:
      return -1

