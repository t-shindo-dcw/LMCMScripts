#!/usr/bin/env python


import subprocess
from datetime import datetime
import socket
import sys
import base64
import time
import os.path

def main():
   #while (True):
	home_dir = os.path.expanduser("~")
	pattern_dir = os.path.join(home_dir, "/lmc/pattern/LMC_FC_128x192.dat ")

	#SunriseTime=datetime(2018, 12, 26, 13, 50, 0)
	SunriseTime=datetime(2019, 1, 1, 7, 12, 0)
        prev= datetime.now()
        while (True):
		now = datetime.now()
		Diff=now-prev
		if (Diff.seconds>=5):
		   break
		string = u'lmcCmd_showmessage '
		string += u'\"<color=\"gray\">現在時刻\n'
		string += u'<color=\"green\">{0:0>2d}:{1:0>2d}:{2:0>2d}'.format(now.hour, now.minute, now.second)
		string += u'\"'
		string += u' -i1 -F/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf -ch -T"+pattern_dir+" -C#ff0000 -S14 -at32 -w '
		SendMessage(string)
		time.sleep(0.1)

       
	now = datetime.now()
	if (SunriseTime>now):
		SunriseDiff=SunriseTime-now
		DiffTotalSeconds=SunriseDiff.seconds +60
		#print DiffTotalSeconds
		DiffHour=DiffTotalSeconds/3600
		DiffTotalSeconds%=3600
		DiffMinute=DiffTotalSeconds/60
		DiffTotalSeconds%=60
		DiffSecond=DiffTotalSeconds

		string = u'lmcCmd_showmessage '
		string += u'\"<color=\"gray\">日の出まで\n'
		string += u' あと<color=\"pink\">{0:0>2d}<color=\"gray\">分'.format(DiffMinute)
		string += u'\"'
		string += u' -i1 -F/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf -ch -T"+pattern_dir+" -C#ff0000 -S13 -at32 -w '

		SendMessage(string)
		time.sleep(5)
	else:
		SunriseDiff=now-SunriseTime
		DiffTotalSeconds=SunriseDiff.seconds
		DiffHour=DiffTotalSeconds/3600
		DiffTotalSeconds%=3600
		DiffMinute=DiffTotalSeconds/60
		DiffTotalSeconds%=60
		DiffSecond=DiffTotalSeconds

		string = u'lmcCmd_showmessage '
		string += u'\"<color=\"pink\">日の出から\n'
		string += u' 　　<color=\"red\">{0:0>2d}<color=\"pink\">分'.format(DiffMinute)
		string += u'\"'
		string += u' -i1 -F/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf -ch -T"+pattern_dir+" -C#ff0000 -S13 -at32 -w '

		SendMessage(string)
		time.sleep(5)


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
		     print returndata
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
