#!/usr/bin/env python3
# -*- coding: utf-8 -*-

###############################################################################
# LMC-01 RPI Tutorial Scripts on Linux-Python
# drawimage.py : Draw Picture
# Ver.0.3 2016/03/02
#
# (C) Kyowa System Co.,ltd. Takafumi Shindo
###############################################################################

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from PIL import ImageSequence
import datetime
import os
import sys
#import ConfigParser
import configparser
import math
import shutil

sys.path.append("./")

import lmc_common

COMMANDHELP = """
#################################################
# drawpicture.py : Draw GIF AnimationPicture
# Kyowa System Co.,ltd.
#################################################

python drawimage.py [File] [command]

■コマンドリスト
 --base-h(default): 画面横を基準に、縦横比を保存して縮小を行う
 --base-v         : 画面縦を基準に、縦横比を保存して縮小を行う
 --rotate-90       : 画像を反時計回りに90度回転する
 --rotate-180      : 画像を反時計回りに180度回転する
 --rotate-270      : 画像を反時計回りに270度回転する
 --centering     : 自動画像センタリングする。
 -PX             : 画像の描画起点を右にずらす ex)-PX-5
 -PY             : 画像の描画起点を下にずらす ex)-PY12
 -I              : 画像のループ回数を指定する。0で無限ループ
 -O              : 出力される画像の名称を指定する。
 -T              : 画像のテンプレートを手動で指定する。
 --quiet          : 画像変換コード

"""

class DrawImageParameter:
    xpos = 0
    ypos = 0
    loopCount = 0
    rotate = 0
    picturePath = None                  #素材ファイルのパスを指定
    destinationPath = None              #出力ファイルのパスを指定
    formatImageFilePath = None          #フォーマットした画像ファイルパスを指定。静止画変換の場合はdestinationPathと同一のデータを書き込む。
    imageSize = (64,32)
    tileCount = 32
    thumbnailBase = "horizontal"
    aa_enable = False
    backgroundColor = '#000000'
    centering = False
    scrollVertical = False
    scrollHorizontal = False

    currentPatternPath = None   #現在使用するテンプレートパターンファイルのパス

    def __init__(self):
        self.dstart = datetime.datetime.now()



class DrawImageScriptConfig(lmc_common.ScriptConfig):

    def __init__(self):
        super(DrawImageScriptConfig,self).__init__()

        self.lmcHomePath = os.path.abspath(os.path.dirname(__file__))

        config = configparser.ConfigParser()
        config.read(self._ConfigFileName)

        self._configTag = "Drawimage"
        self.outputImageName = config.get(self._configTag,'outputimagename')

        self._BaseConfigTag = "LEDControl"

        self.tmpPath = os.path.join(config.get(self._BaseConfigTag,'tmp_path'))
 
        self.splittedTempImageFilePath = os.path.join(self.get_TempWorkPath(),r"spl.bmp")
        self.formatPictureFilePath = os.path.join(self.get_TempWorkPath(),r"tmp.bmp")

        del config

    ################################# get_OutputImagePath ####################################
    # lmi画像出力パスを取得する。
    # 基本的にテンポラリディレクトリのimageディレクトリに画像を出力する。絶対パスが指定されていた場合はそれを優先する。
    ##########################################################################################
    def get_OutputImagePath(self,sourcepath=None):

        if(sourcepath is None):
            resultPath = self.outputImageName
        else:
            resultPath = sourcepath

        if os.path.isabs(resultPath) == False:
            resultPath = os.path.join(self.get_TempImagePath(),resultPath)

        print ("Select OutputImageFile:",resultPath)
        return resultPath

    def get_TempWorkPath(self):
        return os.path.join(self.tmpPath,"work")

def draw_image(argvs):

    #スクリプト設定構造体
    disConfig = DrawImageScriptConfig()

    #基礎データ構造体
    dip = DrawImageParameter()
    dip.destinationPath = disConfig.get_OutputImagePath()
    
    #作業フォルダ作成
    lmc_common.createDirectory(disConfig.tmpPath) #TMPFOLDER)

    dip.loopcount = 1
    rootname = r""

    #GIFフラグ
    gifanimation = False

    argc = len(argvs) # 引数の個数

    if argc == 0:
        #コマンドヘルプを表示する
        print (COMMANDHELP)
        return "";

    currentPatternPath=None
    if (disConfig.multiPatternFile!=""):
        currentPatternPath=lmc_common.GetSpecifiedMultiPatternFile(disConfig,disConfig.multiPatternFile)
            
    if (currentPatternPath==None):
        currentPatternPath=lmc_common.SearchPatternFromFile(disConfig,disConfig.patternFile)

    for arg in argvs:
        #ここにコマンドライン引数による分岐処理を組み込む
        if arg.startswith("--base-h"):
            #縮小基準を横に
            dip.thumbnailBase ="horizontal"
        elif arg.startswith("--base-v"):
            #縮小基準を縦に
            dip.thumbnailBase ="vertical"
        elif arg.startswith("--dbd"):
                #ドットバイドットで表示
            dip.thumbnailBase ="dotbydot"
        elif arg.startswith("--fill"):
                #画面全体にリサイズして表示
            dip.thumbnailBase ="fill"
        elif arg.startswith("--aadisable"):
            #アンチエリアシング不可
            dip.aa_enable = False
        elif arg.startswith("--aaenable"):
            #アンチエリアシング許可
            dip.aa_enable = True
        elif arg.startswith("--centering"):
                #自動センタリング
            dip.centering = True
        elif arg.startswith("--rotate-90"):
            dip.rotate = 90
        elif arg.startswith("--rotate-180"):
            dip.rotate = 180
        elif arg.startswith("--rotate-2"):
            dip.rotate = 270
        elif arg.startswith("-I"):
            #ループ回数指定
            dip.loopcount = int(arg.replace('-I',""))
        elif arg.startswith("-O"):
            #出力ファイル名称
            dip.destinationPath = disConfig.get_OutputImagePath(arg.replace('-O',""))
        elif arg.startswith("-PX"):
            dip.xpos = int(arg.replace('-PX',""))
        elif arg.startswith("-PY"):
            dip.ypos = int(arg.replace('-PY',""))
        elif arg.startswith("-T"):
            #パターン指定
            tmpPatternPath = arg.replace('-T',"")
            print ("Specified single template " , tmpPatternPath )
            currentPatternPath=lmc_common.SearchPatternFromFile(disConfig,tmpPatternPath)
        elif arg.startswith("-sc"):
            dip.scrollHorizontal = True
        elif arg.startswith("-sv"):
            dip.scrollVertical = True
        elif arg.startswith("-t"):
            #マルチパターン指定
            tmpMultiPatternPath = arg.replace('-t',"")
            print ("Specified multi template " , tmpMultiPatternPath)

            ResultPath=lmc_common.GetSpecifiedMultiPatternFile(disConfig,tmpMultiPatternPath)
            if (ResultPath!=None):
                currentPatternPath=ResultPath
        else:
            #ファイルであり、特殊な引数ではない場合、画像ファイルパスであるものとしてpicturepathに格納する
            #第一引数は必ず自分自身のファイル名なので、.pyファイルの名前だった場合スキップ
            tmppicturepath = arg
            
            tmppicturepath = tmppicturepath.replace('\r',"")
            tmppicturepath = tmppicturepath.replace('\n',"")
            
            if os.path.isabs(tmppicturepath) == False:
               result = lmc_common.SearchImageFile(disConfig,tmppicturepath)
               if result != None:
                 tmppicturepath = result
            
            print (disConfig.get_LocalImagePath(),tmppicturepath)
            
            if os.path.isfile(tmppicturepath):
              root, ext = os.path.splitext(tmppicturepath)
              if ext != ".py" and ext != ".PY":
                dip.picturePath = tmppicturepath
  

    if dip.picturePath is None:
        message = u"Not correct Image File. Please type like 'lmcCmd_showimage [filename]'"
        print (message)
        return None

    #テンプレート読込
    templatesize = lmc_common.detect_xmltemplate(currentPatternPath ,None)
    if (templatesize==None):
        return None
    if len(templatesize) == 5:
        dip.imageSize = (templatesize[2], templatesize[3])
        dip.tileCount = templatesize[4]

    tmpfolder_Format = os.path.join(disConfig.get_TempWorkPath(),r"tmp") 
    if os.path.exists(tmpfolder_Format) == False:
        os.mkdir(tmpfolder_Format)



    while os.path.exists(dip.destinationPath):
        os.remove(dip.destinationPath)

    #静止画なのでformatImageFilePathとdestinationPathが同一となる。
    dip.formatImageFilePath = dip.destinationPath
    resultpath = drawimage_normal(dip,disConfig)

    return resultpath

def drawimage_normal(dip,disConfig):

    result = None

    if os.path.isfile(dip.picturePath):
        file, ext = os.path.splitext(dip.picturePath)
        if ext in [".jpg",".jpeg",".JPG",".JPEG",".png",".PNG",".bmp",".BMP"]:
            im = Image.open(dip.picturePath)
        else:
            errormessage = "".join([u"File:",dip.picturePath,u" is not a supported file."])
            print (errormessage)
            return None
    else:
        errormessage = "".join([u"path:",dip.picturePath,u" is not found."])
        print (errormessage)
        return None

    if im is not None:
        #イメージ変換、disConfig.formatPictureFilePathで指定される変換済みBMPファイルを作成
        result = create_formatImage(im,dip,disConfig)
        del im

    return result

    
#与えられたSourceImageから、disConfig.formatPictureFilePathで指定される変換済みlmiファイルを作成
def create_formatImage(sourceImage,dip,disConfig):

        #if os.path.exists(disConfig.splittedTempImageFilePath) == True:
        #    os.remove(disConfig.splittedTempImageFilePath)

        # フレームバッファの幅と高さ
        framebuffer_width = dip.imageSize[0]
        framebuffer_height = dip.imageSize[1]

        # 左右オフセット座標
        offset_x = dip.xpos
        offset_y = dip.ypos

        im_frame = sourceImage.convert("RGB")

        # 画像を回転
        rotated_image = im_frame.rotate(dip.rotate, expand=True)

        # 画面内に収めるためにリサイズ
        rotated_width=rotated_image.width
        rotated_height=rotated_image.height

        print("Rotated image size " ,rotated_width,rotated_height)

        if "vertical" in dip.thumbnailBase:
            nx = int(math.ceil(dip.imageSize[1] * rotated_width / rotated_height))
            newsize = (nx,dip.imageSize[1])
                        
        elif "horizontal" in dip.thumbnailBase :
            ny = int(math.ceil(dip.imageSize[0] * rotated_height / rotated_width))
            newsize = (dip.imageSize[0],ny)
        elif "dotbydot" in dip.thumbnailBase :
            newsize = (rotated_width,rotated_height)
        elif "fill" in dip.thumbnailBase :
            newsize = (framebuffer_width,framebuffer_height)
        else :
            newsize = dip.imageSize    

        if (newsize[0] > framebuffer_width * 2 ) and (newsize[1] > (framebuffer_height * 2)):
            print ("Image oversized")
            if (newsize[1] > newsize[0]):
                print (" fit to horizontal")
                ny = int(math.ceil(dip.imageSize[0] * rotated_height / rotated_width))
                newsize = (dip.imageSize[0],ny)
            else:
               print (" fit to vertical ")
               nx = int(math.ceil(dip.imageSize[1] * rotated_width / rotated_height))
               newsize = (nx,dip.imageSize[1])

        FrameBufferSize = framebuffer_width * framebuffer_height * 3
        maximum_size = 0x4000000
        if (FrameBufferSize > maximum_size):
            print ("Image data oversized")
            newsize = (framebuffer_width,framebuffer_height)



        print("Resized image size " ,newsize[0],newsize[1])

        if "dotbydot" in dip.thumbnailBase :
            pass
        #elif "fill" in dip.thumbnailBase :
        else :
            # extend to screen
            print("Resize screen to resized image size (NOT keep aspect ratio)")
            if dip.aa_enable :
                rotated_image = rotated_image.resize(newsize,Image.ANTIALIAS)
            else:
                rotated_image = rotated_image.resize(newsize)

        


        paste_x = 0
        paste_y = 0
        print("Offset size " ,offset_x,offset_y)

        if (dip.centering):
           if (dip.scrollHorizontal) :
               pass
           else:
               print("X axis centering")
               paste_x = (framebuffer_width - rotated_image.width) // 2
           if (dip.scrollVertical) : 
               pass
           else:
               print("Y axis centering")
               paste_y = (framebuffer_height -rotated_image.height) // 2

        paste_x = paste_x + offset_x
        paste_y = paste_y + offset_y
        print("Image paste position " ,paste_x,paste_y)

        ImageWidth=rotated_image.width+paste_x
        ImageHeight=rotated_image.height+paste_y
  
        FinalImageSize=[ImageWidth,ImageHeight]
        print("Final image size " ,ImageWidth,ImageHeight)


        imgbase = Image.new('RGB', FinalImageSize, dip.backgroundColor)
        imgbase.paste(rotated_image, (paste_x, paste_y))

        imgbase.save(disConfig.splittedTempImageFilePath)

        imgbase.close()
        del imgbase

        # bmpからlmiに変換
        shutil.move(disConfig.splittedTempImageFilePath,dip.formatImageFilePath)

        return dip.formatImageFilePath

