#!/usr/bin/env python3
# -*- coding: utf-8 -*-

###########################################################################################

#
# (C)D Craftwork  Takafumi Shindo
###########################################################################################

import os
import socket
import sys
import subprocess
import filecmp
import shutil

from sys import platform

compiledbinary=False

def main():
    global compiledbinary
    print ("multinodestartup.py start")
    print (" Platform :",platform)

    if platform == "win32":
        compiledbinary= True
        CurrentDrectory= os.path.abspath(os.path.dirname(__file__)) 
        OriginalPatternPath=os.path.join(CurrentDrectory,"pattern")
        PatternPathList=os.path.split(CurrentDrectory)
        #PatternPathList=PatternPathList[:-1]
        TargetPatternPath=os.path.join(PatternPathList[0],"patterntemp")
    elif platform == "linux" or platform == "linux2":
        compiledbinary= False
        CurrentDrectory= os.path.abspath(os.path.dirname(__file__)) 
        OriginalPatternPath=os.path.join(CurrentDrectory,"pattern")
        TargetPatternPath=os.path.join(CurrentDrectory,"user")
    TemporaryConfigName="LMCConfig.temp"
    TargetConfigName="LMCConfig.json"
    TemporaryPatternName="TemporaryPattern.dat"

    argvs = sys.argv  
    argc = len(argvs)

    if (argc<=1):
       print ("No pattern file spedified. Abort.")
       return

    MultiPatternName=argvs[1] # Pattern file
    if (argc>2):
        OriginalPatternPath=argvs[2]
    if (argc>3):
        TargetPatternPath=argvs[3]
    
    print ("LMC multipattern file : " , MultiPatternName)
    print ("LMC multipattern source path ",OriginalPatternPath)
    print ("LMC multipattern target path ",TargetPatternPath)
    print ("LMC multipattern config file : " , TargetConfigName)


    print("Detect network slave nodes")
    CreateAssignedMultiPattern(MultiPatternName,OriginalPatternPath,TargetPatternPath,TemporaryConfigName,TargetConfigName,TemporaryPatternName)
    sys.exit()


########################### Slave server #########################
#   SlaveServerを起動
###############################################################################


def CreateAssignedMultiPattern(MultiPatternName,OriginalPatternPath,TargetMultiConfigPath,TemporaryConfigName,TargetConfigName,TemporaryPatternName):
    global compiledbinary
    # JSONファイルのIP,ID対応表に従い、MultiPatternNameのXMLを改変して出力する 
    if (MultiPatternName==""):
        return ""


    OriginalPatternPathName=os.path.join(OriginalPatternPath,MultiPatternName)
    TargetMultiPatternPathName=os.path.join(TargetMultiConfigPath,MultiPatternName)
    TemporaryMultiConfigPathName=os.path.join(TargetMultiConfigPath,TemporaryConfigName)
    TargetMultiConfigPathName=os.path.join(TargetMultiConfigPath,MultiPatternName)
    TemporaryMultiPatternPathName=os.path.join(TargetMultiConfigPath,TemporaryPatternName)

    if not os.path.exists(OriginalPatternPathName):
         return TargetMultiPatternPathName

    print ("Original pattern path :",OriginalPatternPathName)
    print ("Target template File : ",TargetMultiPatternPathName)

    ScanCurrentSlaves(TemporaryMultiConfigPathName,TargetMultiConfigPathName)
    if not os.path.exists(TargetMultiConfigPathName):
       return OriginalPatternPath

    print ("Start to create XML File from IP config file.")
    print ("Using template File : ",OriginalPatternPathName)

    if platform == "win32":
      if compiledbinary:
         SlaveIsAllReady=subprocess.call(["lmcJSONtoXML.exe",TargetMultiConfigPathName,OriginalPatternPathName,TemporaryMultiPatternPathName], shell=False)
      else:
         SlaveIsAllReady=subprocess.call(["python3","lmcJSONtoXML.py",TargetMultiConfigPathName,OriginalPatternPathName,TemporaryMultiPatternPathName], shell=False)
    elif platform == "linux" or platform == "linux2":
      SlaveIsAllReady=subprocess.call(["sudo","python3","lmcJSONtoXML.py",TargetMultiConfigPathName,OriginalPatternPathName,TemporaryMultiPatternPathName], shell=False)


    if os.path.exists(TemporaryMultiPatternPathName):
               # Userフォルダにコピーを行う。
               # UserフォルダのPatternファイルと比較して、不一致ならば上書きする。
               print ("User temporary template File : ",)

               if not os.path.exists(TargetMultiPatternPathName):
                   print ("Update user template file")
                   shutil.copy(TemporaryMultiPatternPathName,TargetMultiPatternPathName)
               elif (not filecmp.cmp(TemporaryMultiPatternPathName, TargetMultiPatternPathName,False)):
                   print ("Update user template file")
                   shutil.copy(TemporaryMultiPatternPathName,TargetMultiPatternPathName)
               # Userフォルダ内部へのパスを返す 
               return TargetMultiPatternPathName
    else:
       return ""


def ScanCurrentSlaves(TemporaryMultiConfigPathName,TargetTempConfigPathName):
 
    #print "DEBUG: ScanCurrentSlaves()"
    # SlaveのIPを検索して、Configファイルを作成する。
 
    # Network上のSlaveをスキャンして、JSONファイルを生成する。 
    global compiledbinary
    if platform == "win32":
      if compiledbinary:
          createdsubprocess=subprocess.Popen(["lmclanscantoJSON.exe",TemporaryMultiConfigPathName], shell=False)
      else:
          createdsubprocess=subprocess.Popen(["python3","lmclanscantoJSON.py",TemporaryMultiConfigPathName], shell=False)
    elif platform == "linux" or platform == "linux2":
      createdsubprocess=subprocess.Popen(["sudo","python3","lmclanscantoJSON.py",TemporaryMultiConfigPathName], shell=False)

    createdsubprocess.wait()

    if not os.path.exists(TemporaryMultiConfigPathName):
        print ("Config pattern is not ready")
        return

    if not os.path.exists(TargetTempConfigPathName):
        print ("Update user slave configuration file")
        shutil.copy(TemporaryMultiConfigPathName,TargetTempConfigPathName)
    elif (not filecmp.cmp(TemporaryMultiConfigPathName, TargetTempConfigPathName,False)):
        print ("Update user slave configuration file")
        shutil.copy(TemporaryMultiConfigPathName,TargetTempConfigPathName)

########################## MAIN #############################

if __name__ == "__main__":

        main()