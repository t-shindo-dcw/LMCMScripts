#!/usr/bin/env python3

###########################################################################################
# LMC network scan of slaves 
#
# (C) Kyowa System Co.,ltd. Keisuke Shindo
###########################################################################################

import os
import socket
import sys
import json
import struct

import datetime
from sys import platform

FoundHostList={}
SendPacket=None
Port=49200


def main():
        global FoundHostList
        global SendPacket
        global Port
        global logger

        argvs = sys.argv  
        argc = len(argvs)

        # Debug log mode
        #logger = initialize_logger('logger_command')

#       host = socket.gethostbyname(socket.gethostname())

        TargetJSONFileName="AssignedIP.json"

        if (argc<2):
           # Not enough parameters
           print ('Usage: # python %s TargetJSONFile [port] ' % argvs[0])
           quit()         # プログラムの終了
        if (argc>1):
           TargetJSONFileName=argvs[1] # JSON file

        if (argc>2):
           Port = int(argvs[2]) # Port number

        print ("lmclanscantoJSON.py start")
        print ("JSON target file : " , TargetJSONFileName)
        print ('Port : %d ' % Port)

        # Binary message
        SendPacket=CreateSendPacket()

        IfFound=False

        try :
           if platform == "win32":
              host=socket.gethostname()
              hosteth0=socket.gethostbyname(host)
           elif platform == "linux" or platform == "linux2":
              hosteth0 = os.popen('ip addr show eth0').read().split("inet ")[1].split("/")[0]
        except IndexError:
           hosteth0=None
           print (" eth0 IPv4 address not found")
   
        if (hosteth0 !=None):
           IfFound=True
           print ("Start IP scan from eth0 ",hosteth0)
           IPAddress=hosteth0.split('.')
           for i in range(2,254):
                #if IfFound:
                #       if (str(i)==IPAddress[3]):
                #               #print "DEBUG : Skip ip " , i
                #               continue
                ModifiedIPAddress='.'.join([IPAddress[0],IPAddress[1],IPAddress[2],str(i)])
                ScanIPAddress(ModifiedIPAddress)
                #if (str(i)==IPAddress[3]):
                #   IfFound=True

        if not IfFound :
           try :
              if platform == "win32":
                 hostwlan0 = None
              elif platform == "linux" or platform == "linux2":
                 hostwlan0 = os.popen('ip addr show wlan0').read().split("inet ")[1].split("/")[0]
           except IndexError:
              hostwlan0=None
              print (" wlan0 IPv4 address not found")
           if (hostwlan0 !=None):
              IfFound=True
              print ("Start IP scan from wlan0 ",hostwlan0)
              IPAddress=hostwlan0.split('.')
              for i in range(2,254):
                   #if IfFound:
                   #       if (str(i)==IPAddress[3]):
                   #               #print "DEBUG : Skip ip " , i
                   #               continue
                   ModifiedIPAddress='.'.join([IPAddress[0],IPAddress[1],IPAddress[2],str(i)])
                   ScanIPAddress(ModifiedIPAddress)
                   #if (str(i)==IPAddress[3]):
                   #   IfFound=True
                        
        if (IfFound):
           print ("Found IP List")
           for ID,IPAddress in FoundHostList.items():
               print (" ",IPAddress,":",ID)
 
           # XMLを読み込んで、TempPathに出力する。
           # IDの入れ替えに、FoundHostListを使う。

           CreateJSONFile(TargetJSONFileName)
           print ( "Saved to JSON File : ",TargetJSONFileName)
        else:
           print ( "Slave not found : ")


def ScanIPAddress(ModifiedIPAddress):
        global FoundHostList
        global SendPacket
        global Port
        #print "DEBUG: try to connect ",ModifiedIPAddress
        try : 
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.settimeout(0.01)
                code = client.connect_ex((ModifiedIPAddress, Port)) 

                if code == 0:
                        print ("Found slave node : ",ModifiedIPAddress)
                        client.send(SendPacket)

                        while True:
                                response = client.recv(4096)
                                if response == '':
                                        break
                                if ParseReveicedPacket(response,ModifiedIPAddress):
                                        break
                                #else:
                                        #print ("Network error code: ",os.strerror(code))
        except socket.error as error:
                print ("Network error : ",ModifiedIPAddress)
                print ("Error code : ",error.errno)
        finally:
                client.close()

def CreateSendPacket():
        REQ_ReadAssignedID=0x25
        #  // no parameters
        REQ_WriteAssignedID=0x26
        #  // [IDValue 2bytes]
        CMD_Header=1
        CMD_EndCode=2
        Size=2
        Command=1       # ID
        SendPacket = bytearray()
        SendPacket.append(CMD_Header)
        SendPacket.append(REQ_ReadAssignedID)
        SendPacket.append(Size&0xff)
        SendPacket.append((Size>>8)&0xff)
        SendPacket.append((Size>>16)&0xff)
        SendPacket.append((Size>>24)&0xff)
        SendPacket.append(Command&0xff)
        SendPacket.append((Command>>8)&0xff)
        SendPacket.append(CMD_EndCode)
        CreatedPacket=",".join(map(str,SendPacket))

        return SendPacket

def ParseReveicedPacket(ReadData,ModifiedIPAddress):

        REQ_ReadAssignedID=0x25
        #  // no parameters
        REQ_WriteAssignedID=0x26
        #  // [IDValue 2bytes]
        ACK_ReadConfigFile=0x44
        # // [command 2bytes][Data 16bytes]
        CMD_Header=1
        CMD_EndCode=2

        global FoundHostList
        #print "DEBUG : ParseReveicedPacket "

        ReadBytes=struct.unpack('B' * len(ReadData), ReadData)
        #print ",".join(map(str,ReadBytes))
        if (ReadBytes[0]!=CMD_Header):
            return True
        
        if (ReadBytes[1]!=ACK_ReadConfigFile):
            return False
        Command=ReadBytes[2]
        Command+=ReadBytes[3]<<8
        ReadStr=""
        for i in range(4,20):
           if (ReadBytes[i]==0):
               break
           ReadStr+=chr(ReadBytes[i])
        if (ReadStr!=""):
           #ID=int(ReadStr)
           print ("Slave is ready. IP ",ModifiedIPAddress)
           #print "DEBUG : Read from packet : ID ",ReadStr
           FoundHostList[ReadStr]=ModifiedIPAddress
        print (" Received ID data ",ReadStr," from ",ModifiedIPAddress)
        return True

def CreateJSONFile(JSONFileName):

    global FoundHostList

    FileObject = open(JSONFileName , 'w')
    json.dump(FoundHostList,FileObject)

    

########################## MAIN #############################

if __name__ == "__main__":
        main()
