#!/usr/bin/env python3
# -*- coding: utf-8 -*-

###########################################################################################
# Commad sender on Windows-Python
# commandclient.py : LMC Network Command Controller
# Ver.0.1 2018/03/08  by K.Shindo
#
# (C) Kyowa System Co.,ltd. Keisuke Shindo
###########################################################################################

# -*- coding:utf-8 -*-
#coding: UTF-8
import socket
import sys
import base64

def main():
        argvs = sys.argv  
        argc = len(argvs)
        if (argc < 4 ): 
            print ('Usage: # python %s \"lmccommand\"' % argvs[0])
            quit()

        host = socket.gethostbyname(socket.gethostname())
        port=10020

        message=argvs[3] # message
        host = argvs[1] # IP address
        #if (argc>3):
        port = int(argvs[2]) # Port number


        print (u'IP : %s ' % host)
        print (u'Port : %d ' % port)
        print (u'Send message : %s ' % message)
        message=CustomizedReplace(message,' ',chr(0x1f))
        message+="\r"
        print ('Modified message : %s ' % message)

        message=message.encode('utf-8')
        #print (u'Send message before encode: %s ' % message)
        message=base64.b64encode(message)
        #print (u'Send message encoded: %s ' % message)

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        client.connect((host, port)) 

        #client.send(message.encode('UTF-8'))
        client.send(message)

        client.send("\n".encode('utf-8'))

        IfEnded=False
        while True:
             response = client.recv(4096)
             if response == '':
                break
             returndata=response.decode()
             returndata=returndata.split('\n')
             for returncommand in returndata:
                 #print ("Response : ",returncommand)
                 if returncommand == 'Ready.':
                   IfEnded=True
                   break
             if IfEnded:
                break

        client.close()



def CustomizedReplace(InputLine,Separator,ModifiedSeparator):

  InsideQuotation=False
  Escape=False
  ResultString=""
  for char in InputLine:
     if Escape:
       Escape=False
     elif char=='\\':
       Escape=True
       continue
     elif char=='\'' or char=='"' :
       if InsideQuotation:
           InsideQuotation=False
       else:
           InsideQuotation=True
     elif char==Separator:
       if InsideQuotation==False:
           ResultString+=str(ModifiedSeparator)
           continue
     ResultString+=str(char)
  return ResultString


########################## MAIN #############################

if __name__ == "__main__":
        main()
