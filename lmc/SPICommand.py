#!/usr/bin/env python

###########################################################################################
# LMC SPI communication
#    for Raspberry pi series Rasperry PI OS 
#       Ver1.0
################################################################################

import os
import socket
import time
import sys
import spidev


def main():
        argvs = sys.argv  
        argc = len(argvs)

        if (argc<1):
           # Not enough parameters
           print (" Communicate to LMC by SPI interface ")
           print ('Usage: # python %s "Command" SPIPort SPIdevice' % argvs[0])
           quit()


        Command=argvs[1]
# for DEBUG
        print ("SPI command :",Command)

        #Command=Command.lstrip('\"')
        #Command=Command.rstrip('\"')
        Command+="\r\n"

        bus=0
        device=0
        spi=spidev.SpiDev()
        spi.open(bus,device)
        # CPOL CPHA
        # Polarity Low = 0
        # Phase 1st edge =0  2nd edge =1
        spi.mode=0b01
        spi.max_speed_hz=1000000

        CommandUTF8=bytes(Command,'utf-8')
        SendingCommandList=[ord(char) for char in Command ]
        #print ("LMCSPI Command")
        #print(SendingCommandList)

        spi.xfer(SendingCommandList)

        time.sleep(0.01)

        ToReceiveBytes=20
        IfStart=False
        IfEnd=False
        EndCount=0
        ResultString=""
        
        while (IfEnd==False):
                ReceivedBytes=spi.readbytes(ToReceiveBytes)
                ReceivedBytesList=[]
                #print(ReceivedBytes)

                for ReadChar in ReceivedBytes :
# for DEBUG
                        if ReadChar==0:
                             if (IfStart):
                                IfEnd=True
                                break
                             continue
                        else :
                                IfStart=True
                                ReceivedBytesList.append(ReadChar)
                NewString="".join(chr(char) for char in ReceivedBytesList)
                #print(NewString,end="")
                ResultString+=NewString
                EndCount+=1
                if (EndCount>10):
                    break

        if (IfStart):
          print ("Result : ")
          print (ResultString)
        else :
          print ("No response")

 ########################## MAIN #############################

if __name__ == "__main__":
	main()
