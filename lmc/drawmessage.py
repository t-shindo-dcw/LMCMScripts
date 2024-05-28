#!/usr/bin/env python3
# -*- coding: utf-8 -*-

###############################################################################
# LMC-01 RPI Tutorial Scripts on Linux-Python
# scrollmesdraw.py : Draw FreeText and scroll
# Ver.0.2 2016/03/02
#
# (C) Kyowa System Co.,ltd. Takafumi Shindo
###############################################################################

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import datetime
import os
import sys
#import ConfigParser
import configparser
import math
import re

sys.path.append("./")

import lmc_common

COMMANDHELP = """
#################################################
# drawmessage.py : Draw FreeText and scroll
# Kyowa System Co.,ltd.
#################################################

■コマンドリスト
 -F              : 文字に使用するフォントを示す ex)-Fkochi-gothic.ttf
 -C              : 文字の色を示す。ex)-Cred
 -S              : 文字のサイズを示す。ex)-S18
 -PX             : 画像の描画起点を右にずらす ex)-PX7
 -PY             : 画像の描画起点を下にずらす ex)-PY12
 -nocentering     : 自動画像センタリングをOFFにする。
 -I              : 画像のループ回数を指定する。0で無限ループ
 -O              : 出力される画像の名称を指定する。
 -t              : 画像のマルチテンプレートを手動で指定する。
 -T              : 画像のテンプレートを手動で指定する。
 -D              : 縦書き文字ならば'-Dv'　横書き文字ならば'-Dh' 
"""

class DrawMessageScriptConfig(lmc_common.ScriptConfig):

    def __init__(self):
        super(DrawMessageScriptConfig,self).__init__()

        self._configTag = "Drawmessage"

        config = configparser.ConfigParser()
        config.read(self._ConfigFileName)
        self.fontPath =  config.get(self._configTag,'fontpath')
        self.fontSize =  int(config.get(self._configTag,'fontsize'))
        self.fontColor =  config.get(self._configTag,'fontcolor')
        self.fontIndex = 0
        self.centering = False
        self.messageFileName = config.get(self._configTag,'messagefilename')
        self.formatPictureFilePath = os.path.join(self.get_TempWorkPath(),r"tmp.lmi")        
 
        del config

    ################################# get_OutputImagePath ####################################
    # lmi画像出力パスを取得する。
    # 基本的にテンポラリディレクトリのimageディレクトリに画像を出力する。絶対パスが指定されていた場合はそれを優先する。
    ##########################################################################################
    def get_OutputMessagePath(self,sourcepath=None):

        if(sourcepath is None):
            resultPath = self.messageFileName
        else:
            resultPath = sourcepath

        if os.path.isabs(resultPath) == False:
            resultPath = os.path.join(self.get_TempImagePath(),resultPath)

        print ("Select OutputImageFile:",resultPath)
        return resultPath


# Modified by K.Shindo
def draw_messageplain(argvs,logger):

    #通常のBMP文字画像を1フレームだけを作成するコード
    #初期設定　設定ファイル読み込み

    dmsConfig = DrawMessageScriptConfig()

    dstart = datetime.datetime.now()

    #作業フォルダ作成
    lmc_common.createDirectory(dmsConfig.tmpPath)

    #文字描画基準位置
    xpos = 0
    ypos = 0

    #スクロール方向
    IfHorizontalScroll = False
    IfVerticalScroll = False
    IfScrollReverse = False
    IfVerticalText = False
    rotateangle = 0
    Direction = 'ltr'

    SCREEN_SIZE = (64, 32)
    BKGND_COLOR = 'black'
    IfHTMLTAG=True # for DEBUG

    argc = len(argvs) # 引数の個数

    if argc == 0:
        #コマンドヘルプを表示する
        print (COMMANDHELP)
        return "";


    drawString = argvs[0]
    drawString=drawString.lstrip('\"')
    drawString=drawString.rstrip('\"')
    #print (drawString)
    del argvs[0]


    currentPatternPath=None
    if (dmsConfig.multiPatternFile!=""):
        currentPatternPath=lmc_common.GetSpecifiedMultiPatternFile(dmsConfig,dmsConfig.multiPatternFile)

            
    if (currentPatternPath==None):
        currentPatternPath=lmc_common.SearchPatternFromFile(dmsConfig,dmsConfig.patternFile)


    if lmc_common.DEBUGMODE:
      logmessage= " ".join(["drawmessage execute ","args detect"])
      lmc_common.Log(logmessage,logger)

    for arg in argvs:
        #ここにコマンドライン引数による分岐処理を組み込む
        if arg.startswith("-F"):
            #フォント指定があった場合
            dmsConfig.fontPath = arg.replace('-F',"")
            if os.path.isabs(dmsConfig.fontPath) == False:
              result = lmc_common.findfont(dmsConfig.fontPath)
              if result is not None:
                dmsConfig.fontPath = result
            print ("Use FontFile:",dmsConfig.fontPath)
        elif arg.startswith("--centering"):
            #自動センタリング指定
            dmsConfig.centering=True
        elif arg.startswith("-C"):
            #色指定があった場合
            dmsConfig.fontColor = arg.replace('-C',"")
        elif arg.startswith("-S"):
            #サイズ指定があった場合
            dmsConfig.fontSize = int(arg.replace('-S',""))        
        elif arg.startswith("-D"):
            #方向指定があった場合 v,h
            if arg.startswith("-Dv"):
               IfVerticalText = True
               print (" Vertical text mode")
            elif arg.startswith("-Dr"):
               # Rotation角度指定があった場合
               rotateangle = arg.replace('-Dr',"")
               print (" Rotate angle ",rotateangle)
        elif arg.startswith("-PX"):
            #座標指定があった場合 X
            xpos = int(arg.replace('-PX',""))  
        elif arg.startswith("-PY"):
            #座標指定があった場合 Y
            ypos = int(arg.replace('-PY',""))  
        elif arg.startswith("-O"):
            #出力ファイル名称
            dmsConfig.messageFileName = arg.replace('-O',"")
        elif arg.startswith("-T"):
            #パターン指定
            tmpPatternPath = arg.replace('-T',"")
            print ("Specified single template " , tmpPatternPath) 
            currentPatternPath=lmc_common.SearchPatternFromFile(dmsConfig,tmpPatternPath)
        elif arg.startswith("-t"):
            #マルチパターン指定
            tmpMultiPatternPath = arg.replace('-t',"")
            print ("Specified multi template " , tmpMultiPatternPath)

            ResultPath=lmc_common.GetSpecifiedMultiPatternFile(dmsConfig,tmpMultiPatternPath)
            if (ResultPath!=None):
                currentPatternPath=ResultPath

        elif arg.startswith("-sc"):
            IfHorizontalScroll = True
        elif arg.startswith("-sv"):
            IfVerticalScroll = True
        elif arg.startswith("-sr"):
            IfScrollReverse = True
        elif arg.startswith("-HT"):
            IfHTMLTAG=True

    #テンプレート読込
    templatesize = lmc_common.detect_xmltemplate(currentPatternPath,None)
    if (templatesize==None):
        return None
    if len(templatesize) == 5:
        SCREEN_SIZE = (templatesize[2], templatesize[3])
        tilecount = templatesize[4]
    #テキスト方向
    #if IfHorizontalScroll :
    #       if IfVerticalText:
    #          rotateangle= 90
    #       else:
    #          rotateangle= 0
    #elif IfVerticalScroll :
    #       if IfVerticalText:
    #          rotateangle= 0
    #       else:
    #          rotateangle= 270
    #          rotateangle= 0
    if (rotateangle==0):
        rotateangle=0
    if (rotateangle==90):
        rotateangle=90
    if (rotateangle==180):
        rotateangle=180
    if (rotateangle==270):
        rotateangle=270
    else:
        rotateangle=0

    print ("Text rotation angle : "+str(rotateangle))
    print ("Use FontFile:",dmsConfig.fontPath)
    print ("Font size:",dmsConfig.fontSize)
     #文字整形
    drawString = drawString.replace(r"\r", "")
    drawString = drawString.replace(r"\n", "\n")
    drawString = drawString.replace("\\\"", "\"")
    print ("------------Draw message " )
    print (drawString)
    print ("------------Draw message " )

    #フォント読込
    font = lmc_common.open_PILFont(dmsConfig.fontPath,dmsConfig.fontSize,dmsConfig.fontIndex)

    if IfHTMLTAG:
        if IfVerticalText:
           sourceimg = Drawtext_verticalEx(font,SCREEN_SIZE,xpos,ypos,rotateangle,dmsConfig.centering,dmsConfig.fontColor,BKGND_COLOR,drawString)
        else:
           sourceimg = Drawtext_horizontalEx(font,SCREEN_SIZE,xpos,ypos,rotateangle,dmsConfig.centering,dmsConfig.fontColor,BKGND_COLOR,drawString)
    else:
        if IfVerticalText:
           sourceimg = Drawtext_vertical(font,SCREEN_SIZE,xpos,ypos,rotateangle,dmsConfig.centering,dmsConfig.fontColor,BKGND_COLOR,drawString)
        else:
           sourceimg = Drawtext_horizontal(font,SCREEN_SIZE,xpos,ypos,rotateangle,dmsConfig.centering,dmsConfig.fontColor,BKGND_COLOR,drawString)

    # Drawtext modify until here
    if lmc_common.DEBUGMODE:
      logmessage= " ".join(["drawmessage execute ","draw text"])
      lmc_common.Log(logmessage,logger)

    outputFilePath = dmsConfig.get_OutputMessagePath(dmsConfig.messageFileName)


    #作業ファイルパス作成、および古いファイルの削除
    if os.path.exists(outputFilePath) == True:
      os.remove(outputFilePath)

    sourceimg.save(outputFilePath, "BMP")

    if lmc_common.DEBUGMODE:
      logmessage= " ".join(["drawmessage execute ","save lmiimage"])
      lmc_common.Log(logmessage,logger)


    if os.path.getsize(outputFilePath) == 0:
        #print ("作成されたフォーマット済みビットマップファイルが正しく書き込まれていません。書き出し先の指定が誤っている、もしくは容量を超過している可能性があります。")
        print ("Failed to create a bitmapped text image file. ")
        sys.exit()

    print ("Create bitmapped text image file:[ ", outputFilePath ,u" ]")

    lmc_common.getpasttime(dstart,u"Create Formatted TextImage :")

    return outputFilePath

def Drawtext_horizontal(font,SCREEN_SIZE,xpos,ypos,rotateangle,centering,fontcolor,BKGND_COLOR,drawString):

    wh0 = font.getsize(drawString)
    sourcesize = (wh0[0] + xpos,wh0[1] + ypos)
    sourceimg = Image.new('RGB', sourcesize, BKGND_COLOR)
    #サイズ決定
    draw0 = ImageDraw.Draw(sourceimg)
    #wh = draw0.multiline_textsize(drawString, font=font, spacing=1,direction=Direction)
    wh = draw0.multiline_textsize(drawString, font=font, spacing=1)
    del draw0


    # Centering
    centeringoffsetX=0
    centeringoffsetY=0
    if (centering):
       if (wh[0]<SCREEN_SIZE[0]):
          centeringoffsetX=(SCREEN_SIZE[0]-wh[0])//2
       if (wh[1]<SCREEN_SIZE[1]):
          centeringoffsetY=(SCREEN_SIZE[1]-wh[1])//2
    print ('Display centering offset %d ,%d ' %(centeringoffsetX,centeringoffsetY))
    Virtualxpos=xpos+centeringoffsetX
    Virtualypos=ypos+centeringoffsetY

    # Final positon
    SizeX=wh[0]+Virtualxpos
    if (SizeX<SCREEN_SIZE[0]):
        SizeX=SCREEN_SIZE[0]
    SizeY=wh[1]+Virtualyposs
    if (SizeY<SCREEN_SIZE[1]):
        SizeY=SCREEN_SIZE[1]

    #再度描画  
    print ('Display size :%d ,%d ' %(SizeX,SizeY))
    sourcesize = (SizeX,SizeY )
    sourceimg = Image.new('RGB', sourcesize, BKGND_COLOR)
    draw = ImageDraw.Draw(sourceimg)
   
    #文字の書き込み
    draw.multiline_text((xpos, ypos), drawString, font=font,embedded_color=True,fill=fontcolor,spacing=1,align="left")

    if rotateangle == 90:
       sourceimg = sourceimg.transpose(Image.ROTATE_90)
    elif rotateangle == 180:
       sourceimg = sourceimg.transpose(Image.ROTATE_180)
    elif rotateangle == 270:
       sourceimg = sourceimg.transpose(Image.ROTATE_270)

    print ('Draw image outline W/H : %d,%d' %(sourceimg.width,sourceimg.height))

    return sourceimg

def Drawtext_vertical(font,SCREEN_SIZE,xpos,ypos,rotateangle,centering,fontcolor,BKGND_COLOR, drawString):
    RealImageSize=[SCREEN_SIZE[0],SCREEN_SIZE[1]]
    if (rotateangle == 90):
       RealImageSize[1]=SCREEN_SIZE[0]
       RealImageSize[0]=SCREEN_SIZE[1]
    elif (rotateangle == 270):
       RealImageSize[1]=SCREEN_SIZE[0]
       RealImageSize[0]=SCREEN_SIZE[1]

    #sourceimg = Image.new('RGB', RealImageSize, BKGND_COLOR)
    #サイズ決定
    #draw0 = ImageDraw.Draw(sourceimg)

    # サイズ描画
    wh=[0,0]
    x, y = 0, 0
    C_LineOffset=1
    C_Font_Space=1
    char_width_max=0
    for c in drawString:
        char_width, char_height = font.getsize(c)
        char_height+=C_Font_Space+1
        if c == u"\n":
            if (wh[1] < y):
               wh[1]=y
            x += char_width+C_LineOffset
            y = 0
            continue

        y +=char_height
        if char_width_max < char_width:
             char_width_max = char_width

    wh[0]=x+char_width_max
    if (wh[1] < y):
        wh[1]=y

    # Centering
    centeringoffsetX=0
    centeringoffsetY=0
    if (centering):
       if (wh[0]<SCREEN_SIZE[0]):
          centeringoffsetX=(RealImageSize[0]-wh[0])//2
       if (wh[1]<SCREEN_SIZE[1]):
          centeringoffsetY=(RealImageSize[1]-wh[1])//2
    print ('Display centering offset %d ,%d ' %(centeringoffsetX,centeringoffsetY))

    Virtualxpos=xpos+centeringoffsetX
    Virtualypos=ypos+centeringoffsetY

    #del draw0
    SizeX=wh[0]+Virtualxpos
    if (SizeX<RealImageSize[0]):
        SizeX=RealImageSize[0]
    SizeY=wh[1]+Virtualypos
    if (SizeY<RealImageSize[1]):
        SizeY=RealImageSize[1]

    #再度描画  
    print ('Image size (horizontal image) %d ,%d ' %(SizeX,SizeY))
    sourcesize = (SizeX,SizeY )
    sourceimg = Image.new('RGB', sourcesize, BKGND_COLOR)
    draw = ImageDraw.Draw(sourceimg)
   
    #文字の書き込み
    fontwidth,fontheight = font.getsize("　")
    #print ('SizeX : %d xpos :%d char_width_max: %d ,%d ' %(SizeX,xpos,char_width_max,C_LineOffset))
    x= SizeX+Virtualxpos-char_width_max
    y= Virtualypos
    print ('Display initial position :  %d ,%d ' %(x,y))
    maxwidth=0

    InsideBracket=False
    for char in drawString:
        if char == u"\n":
            x -= char_width_max+C_LineOffset
            y = 0
            continue

        char_width, char_height = font.getsize(char)
        draw.text((x, y), char, font=font,fill=fontcolor,embedded_color=True,spacing=C_Font_Space,align="left")

        y +=char_height

    if rotateangle == 90:
       sourceimg = sourceimg.transpose(Image.ROTATE_90)
    elif rotateangle == 180:
       sourceimg = sourceimg.transpose(Image.ROTATE_180)
    elif rotateangle == 270:
       sourceimg = sourceimg.transpose(Image.ROTATE_270)

    print ('Draw image outline W/H : %d,%d' %(sourceimg.width,sourceimg.height))
    return sourceimg




def Drawtext_verticalEx(font,SCREEN_SIZE,xpos,ypos,rotateangle,centering,fontcolor,BKGND_COLOR, drawString):
    RealImageSize=[SCREEN_SIZE[0],SCREEN_SIZE[1]]
    MaxImageSize=[SCREEN_SIZE[0],0]
    Virtualxpos=xpos
    Virtualypos=ypos
    if (rotateangle == 90):
       RealImageSize[1]=SCREEN_SIZE[0]
       RealImageSize[0]=SCREEN_SIZE[1]
       MaxImageSize=[SCREEN_SIZE[1],0]
       Virtualxpos=-ypos
       Virtualypos=xpos
    elif (rotateangle == 180):
       Virtualxpos=-xpos
       Virtualypos=-ypos
    elif (rotateangle == 270):
       RealImageSize[1]=SCREEN_SIZE[0]
       RealImageSize[0]=SCREEN_SIZE[1]
       MaxImageSize=[SCREEN_SIZE[1],0]
       Virtualxpos=ypos
       Virtualypos=-xpos

    #sourceimg = Image.new('RGB', RealImageSize, BKGND_COLOR)
    #サイズ決定
    #draw0 = ImageDraw.Draw(sourceimg)

    # サイズ描画
    wh=[0,0]
    x, y = 0, 0
    C_LineOffset=1
    C_Font_Space=1
    char_width_max=0

    InsideBracket=False
    OnEscape=False
    for char in drawString:
        if InsideBracket:
           if char == u'>':
              InsideBracket=False
           continue
        if OnEscape:
           OnEscape=False
        elif char == u'<':
           InsideBracket=True
           continue
        elif char == u'\\':
           OnEscape=True
           continue

        if char == u"\n":
            if (wh[1] < y):
               wh[1]=y
            x += char_width_max+C_LineOffset
            y = 0
            continue
        elif char == u'\\':
            OnEscape=True
            continue

        char_width, char_height = font.getsize(char)
        char_height+=C_Font_Space+1
        y +=char_height
        if char_width_max < char_width:
             char_width_max = char_width

    wh[0]=x+char_width_max
    if (wh[1] < y):
        wh[1]=y

    # Centering
    centeringoffsetX=0
    centeringoffsetY=0
    if (centering):
       if (wh[0]<SCREEN_SIZE[0]):
          centeringoffsetX=(RealImageSize[0]-wh[0])//2
       if (wh[1]<SCREEN_SIZE[1]):
          centeringoffsetY=(RealImageSize[1]-wh[1])//2
    print ('Display centering offset %d ,%d ' %(centeringoffsetX,centeringoffsetY))

    Virtualxpos=Virtualxpos+centeringoffsetX
    Virtualypos=Virtualypos+centeringoffsetY

    #del draw0
    SizeX=wh[0]+Virtualxpos
    if (SizeX<RealImageSize[0]):
        SizeX=RealImageSize[0]
    if (MaxImageSize[0]>0) and (SizeX>MaxImageSize[0]):
        SizeX=MaxImageSize[0]
    SizeY=wh[1]+Virtualypos
    if (SizeY<RealImageSize[1]):
        SizeY=RealImageSize[1]
    if (MaxImageSize[1]>0) and (SizeY>MaxImageSize[1]):
        SizeY=MaxImageSize[1]


    print ("DEBUG : drawMessageEX")
    #再度描画  
    print ('Image size (vertical image) %d ,%d ' %(SizeX,SizeY))
    sourcesize = (SizeX,SizeY )
    sourceimg = Image.new('RGB', sourcesize, BKGND_COLOR)
    draw = ImageDraw.Draw(sourceimg)
   
    #文字の書き込み
    fontwidth,fontheight = font.getsize("　")
    x= Virtualxpos
    y= Virtualypos
    print ('Display initial position :  %d ,%d ' %(x,y))
    maxwidth=0
    HTMLTAG=""
    InsideBracket=False
    OnEscape=False
    for char in drawString:
        if InsideBracket:
           # parser of < color="#ffffff" >
           if char == u'>':
              InsideBracket=False
              print ("DEBUG: HTMLTAG : ",HTMLTAG)
              FoundCount=HTMLTAG.find(u'color="')
              if (FoundCount>=0):
                 FoundCount+=len(u'color="')
                 ColorCode=HTMLTAG[FoundCount:]
                 FoundCount=ColorCode.find(u'"')
                 if (FoundCount>0):
                    fontcolor=ColorCode[0:FoundCount]
                    print ("DEBUG: ColorCode : ",fontcolor)
              HTMLTAG=""
           else:
              HTMLTAG+=char
           continue
        else:
          if OnEscape:
              OnEscape=False
          elif char == u'<':
              InsideBracket=True
              continue
          elif char == u'\\':
              OnEscape=True
              continue
          if char == u"\n":
              x += char_width_max+C_LineOffset
              y = Virtualypos
              continue

        char_width, char_height = font.getsize(char)
        try :
           draw.text((x, y), char, font=font,fill=fontcolor,embedded_color=True,spacing=C_Font_Space,align="left")
        except ValueError as ex:
           draw.text((x, y), char, font=font,fill="#FF0000",spacing=C_Font_Space,align="left")
           
        y +=char_height

    if rotateangle == 90:
       sourceimg = sourceimg.transpose(Image.ROTATE_90)
    elif rotateangle == 180:
       sourceimg = sourceimg.transpose(Image.ROTATE_180)
    elif rotateangle == 270:
       sourceimg = sourceimg.transpose(Image.ROTATE_270)

    print ('Draw image outline W/H : %d,%d' %(sourceimg.width,sourceimg.height))
    return sourceimg



def Drawtext_horizontalEx(font,SCREEN_SIZE,xpos,ypos,rotateangle,centering,fontcolor,BKGND_COLOR, drawString):
    RealImageSize=[SCREEN_SIZE[0],SCREEN_SIZE[1]]
    MaxImageSize=[0,SCREEN_SIZE[1]]
    Virtualxpos=xpos
    Virtualypos=ypos
    if (rotateangle == 90):
       RealImageSize[1]=SCREEN_SIZE[0]
       RealImageSize[0]=SCREEN_SIZE[1]
       MaxImageSize=[0,SCREEN_SIZE[0]]
       Virtualxpos=-ypos
       Virtualypos=xpos
    elif (rotateangle == 180):
       Virtualxpos=-xpos
       Virtualypos=-ypos
    elif (rotateangle == 270):
       RealImageSize[1]=SCREEN_SIZE[0]
       RealImageSize[0]=SCREEN_SIZE[1]
       MaxImageSize=[0,SCREEN_SIZE[0]]
       Virtualxpos=ypos
       Virtualypos=-xpos

    #sourceimg = Image.new('RGB', RealImageSize, BKGND_COLOR)
    #サイズ決定
    #draw0 = ImageDraw.Draw(sourceimg)

    # サイズ描画
    wh=[0,0]
    x, y = 0, 0
    C_LineOffset=1
    C_Font_Space=1
    char_height_max=0

    InsideBracket=False
    OnEscape=False
    for char in drawString:
        if InsideBracket:
           if char == u'>':
              InsideBracket=False
           continue
        if OnEscape:
           OnEscape=False
        elif char == u'<':
           InsideBracket=True
           continue
        elif char == u'\\':
           OnEscape=True
           continue

        if char == u"\n":
           if (wh[0] < x):
              wh[0]=x
           y += char_height_max+C_LineOffset
           x = 0
           continue
        elif char == u'\\':
           OnEscape=True
           continue

        char_width, char_height = font.getsize(char)
        char_width+=C_Font_Space
        x +=char_width
        if char_height_max < char_height:
             char_height_max = char_height

    wh[1]=y+char_height_max
    if (wh[0] < x):
        wh[0]=x

    #del draw0

    # Centering
    centeringoffsetX=0
    centeringoffsetY=0
    if (centering):
       if (wh[0]<SCREEN_SIZE[0]):
          centeringoffsetX=(RealImageSize[0]-wh[0])//2
       if (wh[1]<SCREEN_SIZE[1]):
          centeringoffsetY=(RealImageSize[1]-wh[1])//2
    print ('Display centering offset %d ,%d ' %(centeringoffsetX,centeringoffsetY))

    Virtualxpos=Virtualxpos+centeringoffsetX
    Virtualypos=Virtualypos+centeringoffsetY

    SizeX=wh[0]+Virtualxpos
    if (SizeX<RealImageSize[0]):
        SizeX=RealImageSize[0]
    if (MaxImageSize[0]>0) and (SizeX>MaxImageSize[0]):
        SizeX=MaxImageSize[0]
    SizeY=wh[1]+Virtualypos
    if (SizeY<RealImageSize[1]):
        SizeY=RealImageSize[1]
    if (MaxImageSize[1]>0) and (SizeY>MaxImageSize[1]):
        SizeY=MaxImageSize[1]

    print ("DEBUG : drawMessageEX")
    #再度描画  
    print ('Display size (vertical image) %d ,%d ' %(SizeX,SizeY))
    sourcesize = (SizeX,SizeY )
    sourceimg = Image.new('RGB', sourcesize, BKGND_COLOR)
    draw = ImageDraw.Draw(sourceimg)
   
    #文字の書き込み
    fontwidth,fontheight = font.getsize("　")
    #print ('SizeX : %d xpos :%d char_width_max: %d ,%d ' %(SizeX,Virtualxpos,char_width_max,C_LineOffset))
    x= Virtualxpos
    y= Virtualypos
    print ('Display initial position :  %d ,%d ' %(x,y))
    maxheight=0
    HTMLTAG=""
    InsideBracket=False
    OnEscape=False
    for char in drawString:
        if InsideBracket:
           # parser of < color="#ffffff" >
           if char == u'>':
              InsideBracket=False
              print ("DEBUG: HTMLTAG : ",HTMLTAG)
              FoundCount=HTMLTAG.find(u'color="')
              if (FoundCount>=0):
                 FoundCount+=len(u'color="')
                 ColorCode=HTMLTAG[FoundCount:]
                 FoundCount=ColorCode.find(u'"')
                 if (FoundCount>0):
                    fontcolor=ColorCode[0:FoundCount]
                    print ("DEBUG: ColorCode : ",fontcolor)
              HTMLTAG=""
           else:
              HTMLTAG+=char
           continue
        else:
          if OnEscape:
              OnEscape=False
          elif char == u'<':
              InsideBracket=True
              continue
          elif char == u'\\':
              OnEscape=True
              continue
          if char == u"\n":
              x = Virtualxpos
              y += char_height_max+C_LineOffset
              continue

        char_width, char_height = font.getsize(char)
        try :
           draw.text((x, y), char, font=font,fill=fontcolor,embedded_color=True,spacing=C_Font_Space,align="left")
        except ValueError as ex:
           draw.text((x, y), char, font=font,fill="#FF0000",spacing=C_Font_Space,align="left")

        x +=char_width

    if rotateangle == 90:
       sourceimg = sourceimg.transpose(Image.ROTATE_90)
    elif rotateangle == 180:
       sourceimg = sourceimg.transpose(Image.ROTATE_180)
    elif rotateangle == 270:
       sourceimg = sourceimg.transpose(Image.ROTATE_270)

    print ('Draw image outline W/H : %d,%d' %(sourceimg.width,sourceimg.height))
    return sourceimg



