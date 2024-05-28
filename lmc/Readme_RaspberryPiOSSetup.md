# RaspberryPi　手動インストール手順
> 2024.5.21  DCraftWork

この例ではrasbperry pi OS 32bitを使用 
　bookworm(V12)は確認。bullseye（V11）はSPIの速度に問題がある模様。
　64bitOSではそのままでは動作せず

# WindowsのraspberryPI　Imagerアプリを使用
Rasberry pi OSを選択して
 RaspianをSDカードへと書き込み

# RaspberryPiを接続
USBキーボード、USBマウス、HDMIディスプレイをRaspberryPiに接続する
LANケーブルを接続　WiFiでもおそらく大丈夫
SDカードを挿入
USB端子に５V電源を接続する。

# RaspberryPiを起動
### Raspberry Pi OSを起動

### 起動後　ウィンドウ画面から
- Country設定　JAPAN以外は未検証
- SelectWiFi　使用しているWiFiを設定　　今後のWiFi設定のために何かを接続する方が良い。
　UpdateSoftwareでLANかWifiに接続してダウンロード
- ローカライズ設定 TOKYO
- ユーザー名はpiで固定。パスワードは任意。

### 再起動

### GUIウィンドウの上のバーからLXTerminalを開く （黒地に'＞_'）

- sudo raspi-config

（RaspberryPi OS bookworm(V12)ではGUIからでもSPIは設定できるが、Raspi-configを使用しなければSPIはなぜか有効化されない）

### メニュー画面からそれぞれの項目を選択

- System options > Boot /Auto login Desktop/Console Autologin
- Interfacing Options > SSH > Enable
- Interfacing Options > SPI > Enable
  System
	Ja_JP.UTF-8を選択

```
- Localisation Options > Change Timezone > Asia > Tokyo
- Wifi Setup  JP(Japan)
```

### 再起動

# アップデートのためにRaspberryPiを有線LAN接続する。
RaspberryPiのLANコネクタにEthernetケーブルを接続

## RaspberryPiにHDMIディスプレイ、キーボードを接続して直接操作する場合

ファームウェアアップデートへ進む

## Windowsなどからネットワーク接続で操作する場合

### WindowのPCのteratermなどからSSHでraspberrypi.localに接続。
　RaspberryPiのIPアドレスを指定する。


### raspberrypi.localドメインが見つからない場合は、RaspberryPiのコンソールから以下のコマンドを入力。

```
> ip a
```
出力結果は以下のようになる。IPアドレス等は環境によって異なる。
```
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host
       valid_lft forever preferred_lft forever
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP group default qlen 1000
    link/ether b8:27:eb:b2:18:5b brd ff:ff:ff:ff:ff:ff
    inet 192.168.43.101/24 brd 192.168.43.255 scope global eth0
       valid_lft forever preferred_lft forever
    inet6 fe80::d0e0:308e:9204:fc4b/64 scope link
       valid_lft forever preferred_lft forever
3: wlan0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc pfifo_fast state DOWN group default qlen 1000
    link/ether b8:27:eb:e7:4d:0e brd ff:ff:ff:ff:ff:ff
```
コマンド出力の中の、eth0のinetアドレスを見れば、192.168.43.101が接続すべきipアドレスとわかる。

### teratermなどで、SSHログインで接続する。
以下の項目を設定してログイン

|項目 |選択/入力|
|----|------|
|TCP/IP host |192.168.43.101(一例)|
|サービス |SSH|
|ユーザー名	|pi|
|パスフレーズ	| raspberry	|


SSHのセキュリティー警告画面が出てきた場合は、`続行`ボタンを押してSSH暗号鍵を生成する。

### ログインが成功すれば次へ。
この時点では、SSHでコンソールに生える。日本語文字は完全に化けていることに注意。

# ファームウェアアップデート
## Update開始
LMCに必要なパッケージをネットワークから取得する。
```
sudo apt-get -y update 
sudo apt-get -y upgrade
sudo apt-get install -y python-dev
sudo apt-get install -y libjpeg-dev
sudo apt-get install -y libfreetype6-dev
sudo apt-get install -y zlib1g-dev
sudo apt-get install -y python-pip
sudo apt-get install -y python3-pip
sudo apt-get install -y mplayer
sudo apt-get install -y ffmpeg
sudo pip3 install pillow --break-system-packages
sudo pip3 install apscheduler --break-system-packages
sudo pip3 install sqlalchemy --break-system-packages
sudo pip3 install pyftpdlib --break-system-packages

```
なお、apschedulerは接続に失敗することが多い。Retryを繰り返すとうまくいくことがある。

## 64bitOSで32bitアプリを動かすために必要

'''
sudo dpkg --add-architecture armhf
sudo apt-get update
'''

## RAMDiskを作成

fstabファイルを編集
```
sudo nano /etc/fstab
```
以下の行をファイルの最後に追加
```
tmpfs /var/tmp tmpfs nodev,nosuid,size=10M 0 0
```

コマンド実行
```
sudo mount -a
```

確認用コマンド実行
```
df -h
```
出力の中に、以下の行が追加されていることを確認
```
tmpfs            10M     0   10M   0% /var/tmp
```
この時点で、LMCのインストールの用意が出来ている。


## この時点でリブートを推奨
```
sudo reboot now
```
