# Linux用ファームウェア利用マニュアル

 2023.9.14 DCraftWork
 

## LMCで使用するRaspberrryPi上のファームウェア
LMCで使用するRaspberryPiの上では、Raspian等のLinuxが動作している。

Linux上で自動起動するCommandServerは、独自プロトコルのTCPソケット通信のコマンドを受信して、LMCの制御を行う。

Windows,Androidで動作するNeCoWin,NeCoAnなどは、内部でCommandServerと通信して、LMCを制御する。NeCoWinのキャプチャ再生モードでは例外的に、LMC上のLEDMultiControlプロセスに対して直接通信を行う。

## LMCのソフトウェア階層図

### シングルモード　静止画、動画、メッセージ再生
```
  Windows NeCoWin/Android NeCoAn
     | TCP command通信
  LMCRPi Linux CommandServer	/home/pi/lmc/lmcserver.sh
     | プロセス生成
  LMCRPi Linux LMC制御		/home/pi/lmc/LEDMultiControl/LEDMultiControl file.bmp -pFC_64x32.dat
     |  SPI
  LMC board
```
### シングルモード　動画キャプチャ、Windows動画再生
```
  Windows  NeCoWin
     | プロセス生成
　Windows LEDMultiControlWin -m 
     | TCP/UDP直接通信
  LMCRPi Linux LMC制御		/home/pi/lmc/LEDMultiControl/LEDMultiControl -s -pFC_64x32.dat
     | SPI
  LMC board
```
### マルチモード　静止画、動画、メッセージ再生
```
  Windows NeCoWin/Android NeCoAn
     | TCP command通信
  Master LMCRPi Linux CommandServer /home/pi/lmc/lmcserver.sh
     | プロセス生成
  Master LMCRPi Linux 	マルチコントロール	/home/pi/lmc/LEDMultiControl/LEDMultiControl -m -tFC_MC4_128x64.ltb
     |  TCP/UDP通信
  Slaves LMCRPi Linux LMC制御　/home/pi/lmc/LEDMultiControl/LEDMultiControl -s	-pFC_64x32.dat
	(CommandServerから起動）
     |  SPI
  LMC board
```
### マルチモード　動画キャプチャ、Windows動画再生
```
  Windows  NeCoWin
     | プロセス生成
　Windows マルチコントロール　LEDMultiControlWin -m -tFC_MC4_128x64.ltb
     |  TCP/UDP直接通信
  Slaves LMCRPi Linux  LMC制御	/home/pi/lmc/LEDMultiControl/LEDMultiControl -s -pFC_64x32.dat
	(CommandServerから起動）
     | SPI
  LMC board
```
### スケジューラモード
```
  Master LMCRPi Linux CommandServer /home/pi/lmc/lmcserver.sh
     | Schedulerプロセス生成
  LMCRPi Linux Scheduler	/home/pi/lmc/scheduler.py schedule.scd　(CommandServerから起動）
     | TCP Command通信（同一RPi内）
  LMCRPi Linux CommandServer	/home/pi/lmc/lmcserver.sh
     | プロセス生成
  LMCRPi Linux 		/home/pi/lmc/LEDMultiControl/LEDMultiControl file.bmp -pFC_64x32.dat
```
# LMC CommandServer

CommandServerは、RaspberryPi上で動作するPythonスクリプト群である。
　
## CommandServerの起動時の動作
1. RaspberryPiに接続されたUSBメモリの検出によるアップデート＋リブート実行
2. WiFiのモード変更に対する、WiFi設定、リブート
3. スレーブノード自動IPアサイン（マルチコントロールモード）
4. TCPポートからのコマンドを受理して、LEDMultiControlなどをリモート動作

## CommandServer アクセス方法

### from LMC RaspberryPi Linux 
LMC上のRaspberryPiの上で、シェルを使用してアクセスする。
```
/home/pi/lmc/lmccommandclient.py
python ./lmccommandclient.py "192.168.2.1" 10020 "lmcCmd_reset"
```
### from Windows

NeCoWinの実行ファイルディレクトリにあるスクリプトを使用する。

> NeCoWin\lmccommandclient.py

実行方法は以下の通り。LMCIPADDRはLMC(マルチコントロールであればマスターLMC）のあるIPアドレスを指定する。

```
cd /home/pi/lmc/
set LMCIPADDR=192.168.11.3
set LMCPORT=10020
py ./lmccommandclient.py %LMCIPADDR% %LMCPORT% "lmcCmd_reset"
```

# CommandServer Command表

### lmcCmd_connect [connectiongroup]
CommandServerに接続する。connectiongroupは省略できる。
### lmcCmd_reset
LMCの全プロセスを停止して、初期状態に戻す。

Slaveだけはマルチモードであれば再起動する。

### lmcCmd_animation [FileName] [Options]
lmvファイルの動画再生。
```
-PX[pixel]		Draw offset from left to right
-PY[pixel]		Draw offset from top to bottom
-t[tile pattern or ltb]		Search and assign slaves
-T[tile pattern]		Use pattern directly
```
上記以外のオプションは、LEDMultiControlに対して直接渡される。

```

例）lmcCmd_animation /home/pi/lmc/user/File_MiyajimaNewYear2019Short.lmv -i1 -TFC_64x32.dat -mo -cl -ab255 -at24 -w -sd2
```

### lmcCmd_showmessage
文字メッセージの再生（静止）

メッセージはテキストで受信する。表示メッセージは"と"の間の文字列となる。

CommandServer内部のPythonスクリプトで画像に自動変換し、LEDMultiControlで表示する。

### lmcCmd_showmessagescroll
文字メッセージの再生（スクロール）

```
-F[fontfilename]
-C[color]
-S[fontsize]
-Dv			Vertical text
-Dr[0,90,180,270]	画面回転　時計回り
-sc			scroll horizontal right to left]
-sv	scroll vertical bottom to top]
-sr			reverse scroll time]
-PX[pixel]		Draw offset from left to right
-PY[pixel]		Draw offset from top to bottom
-t[tile pattern or ltb]		Search and assign slaves
-T[tile pattern]		Use pattern directly
-O[filename]	 出力テンポラリファイル名指定
```
上記以外のオプションは、LEDMultiControlに対して直接渡される。

```
例）lmcCmd_showmessagescroll "<color=\"red\">L<color=\"green\">M<color=\"blue\">C <color=\"white\">LEDマトリックスコントローラ　" -i1 -F/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf -TFC_64x32.dat -C#ffffff -S24 -PY4 -sc -sy -ch --fill -sp1 -ab255 -at24 -w -sd2
```
### lmcCmd_showimage
jpg,pngなどの静止画像の表示（静止）
### lmcCmd_showimagescroll
jpg,pngなどの静止画像の再生（スクロール）

```
--base-h	画面横フィット。縦横比率維持
--base-v	画面縦フィット。縦横比率維持
--dbd		ドット縮小無し。
--fill		画面縦横フィット。
--aadisable	アンチエイリアシング無効
--aaenable	アンチエイリアシング使用
-O[filename]	 出力テンポラリファイル名指定
-PX[pixel]		Draw offset from left to right
-PY[pixel]		Draw offset from top to bottom
-t[tile pattern or ltb]		Search and assign slaves
-T[tile pattern]		Use pattern directly
--rotate-90		画面回転　時計回り90度
--rotate-180		画面回転　時計回り180度
--rotate-270		画面回転　時計回り270度
```
上記以外のオプションは、LEDMultiControlに対して直接渡される。

```
例）lmcCmd_showimage /home/pi/lmc/user/ff.jpg -i1 -TFC_64x32.dat -sX8 -sc -sy -ch --base-v -sp1 -ab255 -at24 -w
```

### lmcCmd_abort
画像停止、画像消去
### lmcCmd_stop
画像停止　画像消去無し
### lmcCmd_blackout
画像消去のみ
### lmcCmd_filelist
/home/pi/lmc/userフォルダにあるファイルリストを取得する。
jpg,png,lmv,scdファイルが対象となる。
### lmcCmd_fontlist
インストールされたフォントリストを取得する。
システムにインストールされたものと、/home/pi/lmc/user/に格納されたものが取得される。
### lmcCmd_patternlist
/home/pi/lmc/patternにあるパターンリストを取得する。
### lmcCmd_showip
LMCが接続されたIPアドレスを取得する。有線LANのIPアドレスか無線LANのIPアドレスかは、WiFiモードに依存する。
### lmcCmd_showfilefreespace　
ファイルシステムの残量をMByte単位で返す
### lmcCmd_cleartmpdir
RAMディスク上のテンポラリファイルを消去する
### lmcCmd_configdump
LMCのConfig情報をすべて取得する。Config情報は以下のファイルに格納されている。

>	/home/pi/lmc/LMCRPIT_config.ini

### lmcCmd_configget [group][parameter]
group,parameterで指定したLMCのConfig情報を取得する。
### lmcCmd_configset  [group][parameter][Value]
group,parameterで指定したLMCのConfig情報をValueに書き換える。
### lmcCmd_configload
ConfigファイルからConfig設定をリロードする
### lmcCmd_date [DateString]
日付を設定する。rfc-3339フォーマット。変更後の時刻が返答される。
```
	例）lmcCmd_date "2006-04-13 14:12:53"
```
注意：RaspebrryPiにはバッテリーバックアップ時計機能が無いため、起動ごとにWindows,Androidなどから設定する必要がある。
### lmcCmd_slavestart
Windowsからのキャプチャモード、あるいはマルチモードで必要なSlaveサーバーをスタートする。
### lmcCmd_slaveend
Slaveサーバーを終了する。
### lmcCmd_thruserverstart
Windowsからのマルチモニタキャプチャモードで使用するThruサーバーをスタートする。

LAN接続、WiFiクライアント接続であれば不要。
### lmcCmd_thruserverend
Thruサーバーを終了する。
### lmcCmd_schedulerstart [SchedulerFile]
指定された.scdスケジュールファイルを動作開始する。
### lmcCmd_schedulerrunning
現在実行中のスケジュールファイルを取得する。以下のメッセージが返答される。
>"Scheduler is running : [SchedulerFile]"
### lmcCmd_schedulerend
現在実行中のスケジュールファイルを停止する。
### lmcCmd_ftpreboot
FTPサーバーをスタートする。
### lmcCmd_ftpkill
FTPサーバーを終了する。
### lmcCmd_removefile [filename]
指定したファイルを消去する。
### lmcCmd_movefile [filename],[targetpath]
指定したファイルを移動する。targetpathは、/home/pi/lmc以下に限定。
### lmcCmd_addwritepermission [filename]
指定したファイルの実行、書き込みパーミッションを変更する。
### lmcCmd_remote [command]
指定したコマンドを実行する。実行コマンドは、/home/pi/lmc/上にある実行ファイルのみ。
### lmcCmd_wifiupdate
設定ファイルの情報を反映して、WiFiの状態を変更する。
### lmcCmd_slave_idassign
ネットワーク上のスレーブIPを検出して、MultiConfigFileにJSONフォーマットで格納する。
### lmcCmd_slave_createpattern
マルチモニタのパターンから、MultiConfigFileを利用して.IPアドレスが指定されたltbファイルを作成する
### lmcCmd_shutdown
LMCのシャットダウンを行う。電源は自動的には切れない。
### lmcCmd_reboot
LMCのリブートを行う。
### lmcCmd_exit
コマンドサーバを終了する。

# LEDMultiContorl　

LMCMultiControlは、RaspberryPi上で動作する、Linux用バイナリ実行ファイルである。C++とSTL、Boostを使用して記述されている。

LEDMultiControlには、LMCの単体制御機能と、マルチコントロールマスタ機能、スレーブ機能の全てが搭載されている。

起動時のコマンド オプション指定によって機能を選択する。

## 単体制御機能
LEDMultiControlをプロセスとして起動することで、RaspebrryPiに直接接続されたLMCでの静止画、動画再生を実行できる。

```
例）/home/pi/lmc/LEDMultiControl/LEDMultiControl file.bmp -pFC_64x32.dat
```

複数のLEDマトリックスの種類、配置に対応するため、パターンデータ（.datファイル）を使用してLEDマトリックスの配置を指定する。

## LMCスレーブノード機能
マルチコントロールにおいて、すべてのスレーブノードLMC上のRaspberryPiで、LEDMultiContorolを１つづつ動作させておく。

CommandServerのConfigファイルをスレーブモードに設定すれば、RaspberryPiの電源をONにするだけでCommandServerによって自動起動される。

```
例）/home/pi/lmc/LEDMultiControl/LEDMultiControl -s -pFC_64x32.dat
```

## マルチコントロールマスタ動作機能

マルチコントロールは、LANで接続された複数のスレーブノード（LMC+RaspberryPi）に対して、１つの画像、動画を自動的に分割表示する機能である。

```
例）/home/pi/lmc/LEDMultiControl/LEDMultiControl -m File.bmp -tFC_MC4_128x64.ltb 
```

.ltbファイルには、スレーブノードの配置およびIPアドレスがXMLファイルで指定されている。

マルチコントロールで動作するLEDMultiControlは、上記のオプション以外はシングルモードのLEDMultiContorolと同じ用法で使用する。スレーブノードに対して自動的に画像を分配する。


## 実行例
> /home/pi/lmc/LEDMultiControl/LEDMultiControl File.bmp -pFC_64x32.dat -sc -cl


# LEDMultiControlWin
Windows上で動作するLEDMultiControl。コンソールアプリとして作成されている。ソースコードは大半がLEDMultiControlと共通。

スレーブモード無し。マスターモードのみ。コマンドはLEDMultiControlと共通。

## リアルタイムキャプチャ機能
`-ca`オプションによるWindows画面のリアルタイム動画キャプチャ機能を持つ。そのほかはLinux用と同等になる。

シングルノードスレーブに対して転送するには、Windowsコンソールから以下のように入力。画面座標も指定している。

```
例1 LEDMultiControlWin -m -ca -pFCRM_8x4.dat File.LMV -mI192.168.2.205 -mX100 -mY100 -mX128 -mY64
```
マルチコントロールでWindowsから転送するには、Windowsコンソールから以下のように入力。
```
例2) LEDMultiControlWin.exe -m -tFC_MC6_192x64.ltb -ca -cX400 -cY400 -cW512 -cH256 -cl -at32
```