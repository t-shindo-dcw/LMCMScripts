#!/usr/bin/env python3

###########################################################################################
# LMC network ID assign to slaves 
#
# (C) Kyowa System Co.,ltd. Keisuke Shindo
###########################################################################################

import os
import socket
import sys
import json

FoundHostList={}
SendPacket=None
Port=49200


def main():
        global FoundHostList
        global SendPacket
        global Port
        argvs = sys.argv  
        argc = len(argvs)

#       host = socket.gethostbyname(socket.gethostname())

        SourceJSONFileName="AssignedIP.json"

        if (argc<2):
           # Not enough parameters
           print (" Read JSON file and assign IDs into LMC slaves")
           print ('Usage: # python %s SourceJSONFile [port] ' % argvs[0])
           quit()         # プログラムの終了
        if (argc>1):
           SourceJSONFileName=argvs[1] # XML file

        if (argc>2):
           Port = int(argvs[2]) # Port number

        print ("JSON target file : " , SourceJSONFileName)
        print (u'Port : %d ' % Port)


        LoadJSONFile(SourceJSONFileName)

        for ID,IPAddress in FoundHostList.items():
            #print "DEBUG : ",IPAddress,":",ID
            AssignIDIntoNetworks(IPAddress,ID)


def AssignIDIntoNetworks(IPAddress,ID):
        global FoundHostList
        global SendPacket
        global Port

        SendPacket=CreateSendPacket(ID)

        #print "DEBUG: try to connect ",IPAddress
        try : 
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(0.1)
            code = client.connect_ex((IPAddress, Port)) 

            if code == 0:
                print ("Found slave node : ",IPAddress)
                client.send(SendPacket.encode('UTF-8'))

                #while True:
                #   response = client.recv(4096)
                #   if response == '':
                #       break
                #   if ParseReveicedPacket(response,ID,IPAddress):
                #       break

        except socket.error as error:
             print ("Network error : ",IPAddress)
             print ("Error code : ",error.errno)
        finally:
             client.close()


def CreateSendPacket(ID):
        REQ_ReadAssignedID=0x25
        #  // no parameters
        REQ_WriteAssignedID=0x26
        #  // [IDValue 2bytes]
        CMD_Header=1
        CMD_EndCode=2
        TotalDataSize=18
        DataSize=16
        CommandCode=1   # ID
        SendPacket = bytearray()
        SendPacket.append(CMD_Header)
        SendPacket.append(REQ_WriteAssignedID)
        SendPacket.append(TotalDataSize&0xff)
        SendPacket.append((TotalDataSize>>8)&0xff)
        SendPacket.append((TotalDataSize>>16)&0xff)
        SendPacket.append((TotalDataSize>>24)&0xff)
        SendPacket.append((CommandCode)&0xff)
        SendPacket.append((CommandCode>>8)&0xff)
        WriteData=bytearray(ID, encoding="utf-8")
        WriteData.extend([0] * (DataSize-len(WriteData)))
        for i in range(0,DataSize):
             SendPacket.append(WriteData[i])
        SendPacket.append(CMD_EndCode)
        #print "DEBUG : Send packet ",",".join(map(str,SendPacket))
        return SendPacket

def ParseReveicedPacket(ReadData,ModifiedID,IPAddress):

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
        #print "DEBUG : Read from packet : ID ",ReadStr
        #print "DEBUG : Compare JSON file ID : ID ",ModifiedID
        if (ReadStr==ModifiedID):
           print ("ID write succeeded  ID : ID ",ModifiedID," to IP ",IPAddress)
           return True

        return False

def LoadJSONFile(JSONFileName):

    global FoundHostList

    FileObject = open(JSONFileName)
    FoundHostList = json.load(FileObject)

########################## MAIN #############################

if __name__ == "__main__":
        main()
