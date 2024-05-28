# LMCM firmware
  LMC,LMCM（LEDマトリックスコントロール）ボードの制御用ソフトウェア群

  LMC,LMCMなどについての詳細はこのサイトを参照のこと https://ksdt.jp/lmcm/

## 新規のRaspianなどのOSからのインストールの手順を示します。

1. [RaspianからのOSインストール](./lmc/Readme_RaspberryPiSetup.md)


2. [LMCファームウェアセットアップ](./lmc/Readme_lmcmanualinstallation.md)

## ファームウェア技術資料

LMCファームウェア　[仕様ドキュメント](./lmc/LMC_CommandServer_Manual.md)



## 改変履歴

### LEDMultiControl 1.36.0
	マルチコントロールタイミング同期の精密化
	マルチコントロールの同期バグ修正による安定化
### lmcpack 1_4_2
	imageの拡大縮小の動作修正
	画像、文字センタリングの修正
	LMC04との両対応
### NeCoWin 2.16.2
	マルチコントロールリスト実装
### LEDMultiControl 1.36.2
	PatternXMLの一部にHex値を使用可能にした
	LEDMatrixの詳細モード設定に対応 
### LEDMultiControl 1.36.3
	MP4動画連続表示の際のメモリリークに対処
### STM Ver1.0.11
	Matrixの詳細設定に対応
	OEPolarityの動作修正
	PWM制御を最適化　画質のシャープさを向上
	高輝度モード追加　PWMは8ビットに低減。
### NeCoWin 2.16.4
	Configウィンドウの動作修正
	高輝度モード対応
	微修正
### NeCoWin Ver2.17
	LayoutEditor導入
	キャプチャ操作の安定化
### LMCTemplateEditor Ver1.0.1
	Layout追加の修正
	COMポートが複数ある場合への対処
### LMCTemplateEditor Ver1.0.2
	Layoutのバグ修正
	USB COMポートが接続されない場合への対処
	レイアウトの文字を最適化
	カスタムLEDマトリクスの情報が反映されないことがあるバグを修正
### NeCoWin 2.17.1
	USB COMポートが接続されない場合への対処
### NeCoWin 2.17.2
	起動直後のUSB COMポートの検出ミスではエラーダイアログを出さない。
### STM Ver1.0.12	2024.1.11
	USB COMポートでの連続画像表示で表示が停止する問題を修正
		完全ではないため、再起動が必要なことがある。
### LMCTemplateEditor Ver1.1 2024.4.4
	Layoutにおける回転の左右を反転
### lmcpack 1_4_3	2024.4.4
	USBアップデータのファイルのパーミッション、日付更新などを修正	
### lmcpack 1_5_0 2024.5.21
	RaspberryPiOS(32bit) Ver12 bookwormへの対応 Pythonスクリプトの更新
