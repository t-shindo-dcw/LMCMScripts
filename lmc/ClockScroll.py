#!/usr/bin/env python


import subprocess
from datetime import datetime
import socket
import sys
import base64
import time
import os.path

def main():
                home_dir = os.path.expanduser("~")
                pattern_dir = os.path.join(home_dir, "/lmc/pattern/LMC_FC_128x192.dat ")

		now = datetime.now()
		string = u'lmcCmd_showmessage '
		string += u'\"<color=\"white\">ただいまの時刻は'
		string += u'<color=\"red\">{0:0>2d}:{1:0>2d}:{2:0>2d}'.format(now.hour, now.minute, now.second)
		string += u'<color=\"white\">です。\"'
		string += u' -sc -i1 -F/usr/share/fonts/opentype/ipafont-mincho/ipamp.ttf -ch -T"+pattern_dir+" -C#ff0000 -S16 -D -sc -sy -at32 '
#		string += u'  -i1 -F/usr/share/fonts/opentype/ipafont-mincho/ipamp.ttf -ch -T"+pattern_dir+" -C#ff0000 -S14 -at32 -w'

		SendMessage(string)
		#time.sleep(5)


def SendMessage(MessageString):

	  	host = socket.gethostbyname(socket.gethostname())
	        port=10020

		message=CustomizedReplace(MessageString,' ',chr(0x1f))
		message+="\r"

		message=message.encode('utf-8')
		message=base64.b64encode(message)

		client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		client.connect((host, port)) 

		client.send(message.encode('UTF-8'))

		client.send("\n".encode('utf-8'))

	        while True:
	             response = client.recv(4096)
	             if response == '':
	                  break
	             returndata=response.decode()
		     print (returndata)
	             if returndata == 'Ready.':
	                  break

		client.close()


def CustomizedReplace(InputLine,Separator,ModifiedSeparator):

  InsideQuotation=False
  ResultString=""
  for char in InputLine:
     if char=='\'' or char=='"' :
       if InsideQuotation:
           InsideQuotation=False
       else:
           InsideQuotation=True

     if InsideQuotation==False:
        if char==Separator:
            ResultString+=ModifiedSeparator
            continue
     ResultString+=char

  return ResultString


########################## MAIN #############################

if __name__ == "__main__":
	main()
