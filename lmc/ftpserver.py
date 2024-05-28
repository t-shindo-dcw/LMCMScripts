#!/usr/bin/env python3
# -*- coding: utf-8 -*-

###############################################################################
# LMC-01 RPI Tutorial Scripts on Linux-Python
# ftpserver.py : FTP Server Control 
# Depend on pyftpdlib.
# Ver.0.3 2016/03/02
# Ver.0.4 2016/03/22
#
# (C) Kyowa System Co.,ltd. Takafumi Shindo
###############################################################################


import os
import sys
import atexit 

from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
import configparser

absscriptdir = os.path.abspath(os.path.dirname(__file__))	#絶対ディレクトリの取得　lmcフォルダになる
sys.path.append(absscriptdir)								#スクリプトのルートにパスを通す

import lmc_common

class ftpScriptConfig(lmc_common.ScriptConfig):

    def __init__(self):
        super(ftpScriptConfig,self).__init__()

        self._configTag = "FTPServer"

        config = configparser.ConfigParser()
        config.read(self._ConfigFileName)

        self.ftpPort = config.get(self._configTag,'ftpport')
        self.ftpUserName = config.get(self._configTag,'username')
        self.ftpPassword = config.get(self._configTag,'pswd')

        del config

########################## onClosing #############################

@atexit.register
def onClosing():

    global fsConfig

    if os.path.exists(fsConfig.get_PIDPath_FTP()) == True:
        os.remove(fsConfig.get_PIDPath_FTP())

    print(">>> LTMServer(FTP):Server Stopped.")

########################## MAIN #############################

if __name__ == "__main__":

    print ("""
################################################
# LEDTileMonitor FTPServer on Debian-Python2.7
#
# Ver.0.4 2016/03/22
################################################
""")

    fsConfig = ftpScriptConfig()

    #PIDファイル作成
    pid = os.getpid()

    if os.path.exists(fsConfig.get_PIDPath_FTP()) == True:
        os.remove(fsConfig.get_PIDPath_FTP())        

    booterrorpath = os.path.join(absscriptdir,'FTPError.txt')
    if os.path.exists(booterrorpath):
        os.remove(booterrorpath)

    try:
        f = open(fsConfig.get_PIDPath_FTP(),'w')
        f.write(str(pid))
        f.close()
    except IOError as ex:
        result =  ex
        f = open(booterrorpath, 'w')
        f.write(ex)
        f.close()


    ADDRESS = ("0.0.0.0",fsConfig.ftpPort)

    if os.path.exists(fsConfig.get_FTPRoot()) == False:
        os.mkdir(fsConfig.get_FTPRoot())

    authorizer = DummyAuthorizer()
    authorizer.add_user(fsConfig.ftpUserName,fsConfig.ftpPassword,fsConfig.get_FTPRoot(),perm="lradfmw")

    #authorizer.add_anonymous(FTP_ROOT)

    ftp_handler = FTPHandler
    ftp_handler.authorizer = authorizer

    try:
        ftpd = FTPServer(ADDRESS,ftp_handler)
        ftpd.serve_forever()
    except OSError:
        print(u">>> LTMServer(FTP):Error Finished. Can't Open Port(" , fsConfig.ftpPort ,u")" )


