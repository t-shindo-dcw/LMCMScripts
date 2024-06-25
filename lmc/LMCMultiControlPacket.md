# LMC
## LEDMultiControl MultiControlインターフェースを用いた接続方法

## Command server事前準備
 CommandServerへとLMC Slaveの動作要求。
 patternはLMCセクションのパターン名を示す。省略されるとデフォルトを使用する。

> lmcCmd_slavestart -p[pattern]

ex: lmcCmd_slavestart -pLMC_S8_64x32.dat

## TCP Packetの内容
複数バイトの値はリトルエンディアン（下位バイトが先）

### Reset request
接続後のリセット

| Byte   | フィールド名     | 説明                          |
|--------|------------------|-------------------------------|
| Byte 0 | CMD_Header=1      | コマンドのヘッダー            |
| Byte 1 | REQ_LMCReset=20     | コマンド			    |
| Byte 2-5 | Length=0       | データ長さ   |
| Byte 6 | CMD_EndCode=2       | エンドコード             |


### Set Parameter
内部パラメータ設定

| Byte   | フィールド名     | 説明                          |
|--------|------------------|-------------------------------|
| Byte 0 | CMD_Header=1      | コマンドのヘッダー            |
| Byte 1 | REQ_SetParameter=17     | コマンド			    |
| Byte 2-5 | Length=6       | データ長さ   |
| Byte 6-7 | CodeID　       | パラメータコード
| Byte 8-11 | Data       | 32bit値              |
| Byte 12 | CMD_EndCode=2       | エンドコード             |


### Send frame info
表示画面(フレームバッファ)サイズの設定
| Byte   | フィールド名     | 説明                          |
|--------|------------------|-------------------------------|
| Byte 0 | CMD_Header=1      | コマンドのヘッダー            |
| Byte 1 | REQ_FrameInfoSend=21     | コマンド			    |
| Byte 2-5 | Length=4       | データ長さ   |
| Byte 6-7 | X       | Xドット数 		|
| Byte 8-9 | Y       | Yドット数              |
| Byte 12 | CMD_EndCode=2       | エンドコード             |

### Initialize request
送信したパラメータの確定要求

| Byte   | フィールド名     | 説明                          |
|--------|------------------|-------------------------------|
| Byte 0 | CMD_Header=1      | コマンドのヘッダー            |
| Byte 1 | REQ_LMCInitialize=16     | コマンド			    |
| Byte 2-5 | Length=0       | データ長さ   |
| Byte 6 | CMD_EndCode=2       | エンドコード             |

### Send frame Raw
画像転送

| Byte   | フィールド名     | 説明                          |
|--------|------------------|-------------------------------|
| Byte 0 | CMD_Header=1      | コマンドのヘッダー            |
| Byte 1 | REQ_SendFrameRaw=32     | コマンド			    |
| Byte 2-5 | Length=可変       | データ長さ   |
| Byte 6-7 | FrameNumber       | フレーム番号(0-0xfff）  |
| Byte 8- | Bitmap data       | ビットマップ画像データ サイズは(Length-2)             |
| Byte N | CMD_EndCode=2       | エンドコード             |

## UDP packetの内容
### SendFrameChange
転送された画像データを表示（動画専用）
| Byte   | フィールド名     | 説明                          |
|--------|------------------|-------------------------------|
| Byte 0 | CMD_Header=1      | コマンドのヘッダー            |
| Byte 1 | REQ_SendFrameChange=130     | コマンド			    |
| Byte 2-5 | Length=4       | データ長さ   |
| Byte 6-8 | FrameNumber       | フレーム番号(0-0xfff）  |
| Byte 9 | CurrentLimit       | 　電流制御値(0-0xff)             |
| Byte 10 | CMD_EndCode=2       | エンドコード             |
### SendSingleFrame
転送された画像データを表示（単一フレーム専用）

| Byte   | フィールド名     | 説明                          |
|--------|------------------|-------------------------------|
| Byte 0 | CMD_Header=1      | コマンドのヘッダー            |
| Byte 1 | REQ_SendSingleFrame=132     | コマンド			    |
| Byte 2-5 | Length=4       | データ長さ   |
| Byte 6-8 | FrameNumber       | フレーム番号(0-0xfff）  |
| Byte 9 | CurrentLimit       | 　電流制御値(0-0xff)             |
| Byte 10 | CMD_EndCode=2       | エンドコード             |


## 画像データの構造
64x48ドットや128x192ドットなどのBMPデータのヘッダを除外した画像部分と同一。「左下」が原点。輝度を示す。8ビットデータで構成され、データのアドレスは以下の順序で右がBit0。
> 　Y座標　X座標　RGB 


##　転送順序
### Initialization
1. TCP ソケット接続 
    AF_INET
    Portは通常49200
2. UDP ソケット接続
    AF_INET SOCK_DGRAM
    Portは通常49201

### Initialize command 
TCPパケットを転送する。
-  (TCP)Reset request
-  (TCP)SetParameter PacketCommand_brightness=1 value=0-255	輝度を設定
-  (TCP)Send frame info (Xdot ,YDot)		LMCのフレームバッファのドット数を指定 192x128など
-  (TCP)InitiallizeRequest

### 動画表示
TCP/UDPパケットを転送する。
-  (TCP)SendFrameRaw		
-  (UDP)SendFrameChange

	UDPは可能であればフレームのタイミングを1/60秒単位で表示時間と合わせて送信すれば厳密。

  FrameNumberは1から転送する画面ごとに1つ増加。0xfffに到達したところで再び1に戻る。
  CurrentLimitは電流制御値。0x0から0xffの間。通常は0x20程度。

### 1frame単体表示
TCP/UDPパケットを転送する。

-  (TCP)SendFrameRaw 
-  (UDP)SendSingleFrame

  FrameNumberは0が基本。転送間は１秒以上のインターバルが必要。
  CurrentLimitは電流制御値。0x0から0xffの間。通常は0x20程度。

### 転送終了処理
1. TCP ソケット切断
2. UDP ソケット切断
