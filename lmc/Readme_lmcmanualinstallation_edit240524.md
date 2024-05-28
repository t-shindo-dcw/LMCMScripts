# LMC　手動インストール手順
    2023.8.29　DCraftWork

すでに動作しているRaspberryPiのシステムに、手動で新規のコマンドサーバー群をインストールする方法です。

RaspberryPi　手動インストール手順の続きとなります。
既存のシステムのアップグレードも可能です。

### LMC関連ファイルのインストール

事前準備

```
 cd /home
 sudo chmod a+w pi
```

`lmcpack.zip`を、RaspberryPiのユーザーディレクトリにコピー。SSHなどを使用。
`lmcpack.zip`は、NeCoWinのインストールディレクトリなどに格納されている。

その後に、以下のコマンドを実行。PCからのSSHログインなどであれば、そのままコマンドラインにペーストしても良い。

```
 cd /home/pi/
 unzip lmcpack.zip
 cd ~/lmc

 sudo chmod +x autosetup.sh
 ./autosetup.sh

```

### コマンドサーバーの自動起動設定 
以下のシェルコマンドを実行して、コマンドサーバーの自動起動を登録する。

```
cd ~/lmc
sudo mv lmcserver.service /etc/systemd/system/
cd /etc/systemd/system
sudo chmod +x lmcserver.service
sudo systemctl enable lmcserver

```
### フォントのインストール
```
sudo apt-get install -y fontconfig 
sudo apt-get install -y fonts-freefont-ttf
sudo apt-get install -y fonts-takao
sudo apt-get install -y fonts-ipafont
sudo apt-get install -y fonts-ipaexfont
sudo apt-get install -y fonts-noto-color-emoji

```

### fontディレクトリの指定
ユーザーディレクトリのフォントを利用可能にする。
```
sudo nano /etc/fonts/fonts.conf




```

    20240524
    local.confを編集しろと警告が出る。
    イカのファイルを/etc/fonts/local.confとして制作するべし。

```
<?xml version="1.0" ?>
<!DOCTYPE fontconfig SYSTEM "font.dtd">
<fontconfig>
        <dir>~/lmc/user</dir>
</fontconfig>
```

以下の記述を探す
```
       <dir>/usr/share/fonts</dir>
        <dir>/usr/X11R6/lib/X11/fonts</dir> <dir>/usr/local/share/fonts</dir>
```
この行の後に、
```
	<dir>~/lmc/user</dir>
```
を追加


### CPU周波数の設定補助
以下のアプリをインストールしてCommandServerからの自動設定を可能にする。
```
sudo apt-get install -y cpufrequtils
```

### config.txtの修正　SPIのマルチポート化
```
sudo nano /boot/firmware/config.txt
```
このファイルの中の以下の記述の次に

```
[pi4]
# Run as fast as firmware / board allows
arm_boost=1
```
以下の記述を追加する。

```
dtoverlay=spi0-1cs 
#dtoverlay=spi1-1cs 

dtoverlay=spi3-1cs 
#dtoverlay=spi4-1cs 
#dtoverlay=spi5-1cs 
#dtoverlay=spi6-1cs 

dtoverlay=spi-bcm2835
```
### RPI4用のSPIのBufferSize拡大 
パスが変わっていたので修正。firmwareディレクトリに入った。
```
sudo nano /boot/firmware/cmdline.txt
```
 以下の記述を改行せずにスペース区切りで追加 
```
 spidev.bufsiz=65536                
```

### bcm2835　SPIライブラリのインストール
```
cd /tmp              
wget http://www.airspayce.com/mikem/bcm2835/bcm2835-1.58.tar.gz                       
tar xvfz bcm2835-1.58.tar.gz                      
cd bcm2835-1.58                       
./configure                      
make        
sudo make install

```

### ffmpegライブラリのインストール　Ver3.3.9が必要
```
cd /tmp
sudo apt update
sudo apt install build-essential cmake git
sudo apt install libx264-dev libx265-dev libv4l-dev libpulse-dev

git clone https://github.com/FFmpeg/FFmpeg.git
cd FFmpeg
export CFLAGS="-march=armv7-a -mfpu=neon-vfpv4"
export CXXFLAGS="-march=armv7-a -mfpu=neon-vfpv4"
export LDFLAGS="-Wl,-rpath /usr/local/lib"
git checkout n3.3.9
./configure --enable-gpl --enable-libx264 --enable-libx265 --enable-nonfree --disable-doc --arch=armhf --target-os=linux --enable-libv4l2 --enable-libpulse --enable-shared
make -j4
sudo make install

```
### libx264.so.138がないのでインストールディレクトリから強制的にコピー
```
sudo cp ~/lmc/libx264.so.138 /lib/arm-linux-gnueabihf/
sudo cp ~/lmc/libx265.so.165 /lib/arm-linux-gnueabihf/
sudo cp ~/lmc/libx264.so.155 /lib/arm-linux-gnueabihf/
```

### 最後に、以下を実行。これが重要。
```
sudo ldconfig

```


### SDカードのフラッシュメモリ保護
swap無効化。Linuxには、自動的に仮想記憶を用いてメモリをSDカードに退避させる機能があるので、それを無効化する。
``` 
sudo swapoff --all
free
sudo apt-get remove -y dphys-swapfile

``` 
以下のコマンドで、swapが無効化されていることを確認。
```
more /proc/swaps
```
出力結果が以下の一行だけで、Swapの中身がなければ成功。
```
Filename                                Type            Size    Used    Priority
```


### ネットワークからのダウンロードがうまくいかない場合
：DHCPの修復　以下のコマンドを実行すれば解決することがある
sudo dhclient eth0
