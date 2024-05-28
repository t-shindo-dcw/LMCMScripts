# LMCM firmware
  LMC,LMCM（LEDマトリックスコントロール）ボードの制御用ソフトウェア群

  LMC,LMCMなどについての詳細はこのサイトを参照のこと https://ksdt.jp/lmcm/

## 改変履歴

 LEDMultiControl 1.36.0
	マルチコントロールタイミング同期の精密化
	マルチコントロールの同期バグ修正による安定化
 lmcpack 1_4_2
	imageの拡大縮小の動作修正
	画像、文字センタリングの修正
	LMC04との両対応
 NeCoWin 2.16.2
	マルチコントロールリスト実装
 LEDMultiControl 1.36.2
	PatternXMLの一部にHex値を使用可能にした
	LEDMatrixの詳細モード設定に対応 
 LEDMultiControl 1.36.3
	MP4動画連続表示の際のメモリリークに対処
 STM Ver1.0.11
	Matrixの詳細設定に対応
	PWM制御を最適化　画質のシャープさを向上
	高輝度モード追加　PWMは8ビットに低減。
 NeCoWin 2.16.4
	Configウィンドウの動作修正
	タイル編集を追加

## 新規のRaspianなどのOSからのインストールの手順を示します。

1. [RaspianからのOSインストール](./Readme_RaspberryPiSetup.md)


2. [LMCファームウェアセットアップ](./Readme_lmcmanualinstallation.md)

## ファームウェア技術資料

LMCファームウェア　[仕様ドキュメント](./LMC_CommandServer_Manual.md)

