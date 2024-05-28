# LMC　手動ネットワークインストール手順
    2023.8.28   DCraftWork

RaspberryPiにWiFiアクセスポイントの機能を追加する手順です。


基本的にはRaspberryPiの公式の手順に従ってアクセスポイントを作成する。

https://www.raspberrypi.com/documentation/computers/configuration.html#setting-up-a-routed-wireless-access-point

NeCoWin,NeCoAnの接続仕様に合わせるためにアクセスポイントから見えるIPアドレスは10.0.0.120とする。以下は、上のサイトとの相違点のみを記述する。


```
sudo nano /etc/dhcpcd.conf
```
エディタで以下を入力してCtrl-Oでセーブ
```
interface wlan0
    static ip_address=10.0.0.120/24
    nohook wpa_supplicant
```

```
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
sudo nano /etc/dnsmasq.conf
```
エディタで以下を入力してCtrl-Oでセーブ

```
interface=wlan0 # Listening interface
dhcp-range=10.0.0.2,10.0.0.20,255.255.255.0,24h
                # Pool of IP addresses served via DHCP
domain=wlan     # Local wireless DNS domain
address=/gw.wlan/10.0.0.1
                # Alias for this router
```

```
sudo nano /etc/hostapd/hostapd.conf
```
エディタで以下を入力してCtrl-Oでセーブ
```
country_code=JP
interface=wlan0
ssid=lmcwlan
hw_mode=g
channel=7
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=LEDMultiControl
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
```
## 

