#!/usr/bin/env python3

###########################################################################################
# Port scanner
#
# (C) Kyowa System Co.,ltd. Keisuke Shindo
###########################################################################################

import os
import socket
import sys
import base64
import xml
import xml.etree.ElementTree as ET
import json
import codecs
from sys import platform

FoundHostList={}

def main():
        global FoundHostList
        argvs = sys.argv  
        argc = len(argvs)


        JSONFileName=""
        TargetXMLFileName=""

        if (argc<=3):
           # Not enough parameters
           print (" Read JSON file and modify LMC pattern XML file")
           print ('Usage: # python %s JSONFile XMLFileName TargeXMLFileName ' % argvs[0])
           quit()         # プログラムの終了

        if (argc>0):
           JSONFileName=argvs[1] # JSON file
        if (argc>1):
           XMLFileName=argvs[2] # XML file

        if (argc>2):
           TargetXMLFileName=argvs[3] # XML file

        print ("JSON IP list file : " , JSONFileName)
        print ("XML source file : " , XMLFileName)
        print ("XML target file : " , TargetXMLFileName)
        LoadJSONFile(JSONFileName)
                        
        #for ID,IPAddress in FoundHostList.items():
        #    print "DEBUG : ",IPAddress,",:",ID
 
        # XMLを読み込んで、TempPathに出力する。
        # IDの入れ替えに、FoundHostListを使う。

        Result=CreateXMLFile(XMLFileName,TargetXMLFileName)
        if Result:
           print ("All slave nodes are ready.")
           print ("Normal end.")
           sys.exit(0)
        else:
           print ("Some slave nodes are not ready.")
           print ("Abnormal end.")
           sys.exit(1)


def LoadJSONFile(JSONFileName):

    global FoundHostList

    FileObject = open(JSONFileName)
    FoundHostList = json.load(FileObject)

def CreateXMLFile(XMLFile,TargetXMLFile):

    global FoundHostList

    DefaultIP=None
    try :
       if platform == "win32":
           host=socket.gethostname()
           DefaultIP=socket.gethostbyname(host)
       elif platform == "linux" or platform == "linux2":
           DefaultIP = os.popen('ip addr show eth0').read().split("inet ")[1].split("/")[0]

       IPAddress=DefaultIP.split('.')
       # Abandon IP  *.*.*.1
       DefaultIP='.'.join([IPAddress[0],IPAddress[1],IPAddress[2],str(1)])
    except IndexError:
       DefaultIP=None
       print (" eth0 IPv4 address not found")
       return


    try:
      tree = ET.parse(XMLFile)
      root = tree.getroot()

      version=int(root.find('VERSION').text)
      #print "VERSION: ",version

      UnassignedBlocks=0
      if version == 4:
        for block in root.findall('BLOCK'):
            CurrentID=-1
            FoundIDElement=block.find("ID")
            if not FoundIDElement==None:
               CurrentID=int(FoundIDElement.text)
               if (CurrentID>0):
                   NewIP=FoundHostList.get(str(CurrentID))
                   print ("Modify XML. Found specified ID ",CurrentID)
                   IfFound=False
                   if (NewIP==None):
                     NewIP=DefaultIP
                     UnassignedBlocks+=1
                   FoundIPElement=block.find('BlockIP')
                   if not FoundIPElement==None:
                      FoundIPElement.text=NewIP
                      print ("Modify XML. Modify BlockIP element. : ID ",CurrentID," : IP ",NewIP)
                   else:
                      NewIPEntry=ET.SubElement(block, 'BlockIP')
                      NewIPEntry.text=NewIP
                      print ("Modify XML. Add new BlockIP element. : ID ",CurrentID," : IP ",NewIP)
      tree.write(TargetXMLFile)
      print ("Modify XML. Write to XML fiile " , TargetXMLFile)
    except:
      return False

    if (UnassignedBlocks>0):
       return False
    return True

########################## MAIN #############################

if __name__ == "__main__":
        main()
