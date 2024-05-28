#!/usr/bin/env python3

###########################################################################################
# LMC supervisor of command server
#
# 
#
###########################################################################################

import socket
import subprocess
import time
import base64
#import RPi.GPIO as GPIO
import pigpio

# プロセスが起動するサーバーのアドレスとポート番号
ProcessName = "commandserver.sh"
host = socket.gethostbyname(socket.gethostname())
port = 10020
IfBreakDetected = False
#SW1,2ボタンの接続先のGPIOピン番号 LMCMでは24，25
BUTTON_PIN = 24  # GPIO port number

def main():
    # メインループ
    print("LMC supervisor started")
    # Start initial process
    start_process()

    print("Process started")
    print("Host ip address : " , host)
    print("Host port : " , port)



    # GPIOの初期化
    #GPIO.setmode(GPIO.BCM)
    #GPIO.setup(BUTTON_PIN, GPIO.IN,pull_up_down=GPIO.PUD_UP)
    # GPIOイベントの監視を開始する
    #GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, callback=button_pressed_callback)

    ## pigpioを使用
    start_pigpio_daemon()
    pi = pigpio.pi()
    pi.set_mode(BUTTON_PIN, pigpio.INPUT)
    pi.set_pull_up_down(BUTTON_PIN, pigpio.PUD_UP)
    pi.callback(BUTTON_PIN, pigpio.FALLING_EDGE, button_pressed_callback)

    while True:
        #if (IfBreakDetected):
        #     time.sleep(1)  # プロセスが再開するまで待機する
        #     continue

        ## ソケットを作成してサーバーに接続する
        #sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #sock.settimeout(60)  # タイムアウトを5秒に設定する
        #try:
        #    sock.connect((host, port))
        #except socket.error:
        #    # 接続に失敗した場合はプロセスを再起動する
        #    print('Cannot connect to server. Restarting process...')
        #    start_process()
        #    time.sleep(10)  # プロセスが起動するまで待機する
        #    continue
        ## サーバーにメッセージを送信して返答を待つ
        #result = SendData("lmcCmd_watchdog")
        #if not result:
        #    # 返答がなかった場合はプロセスを再起動する
        #    print('No response from server. Restarting process...')
        #    killall_Process()
        #    time.sleep(1)  # プロセスが終了するまで待機する
        #    start_process()
        #    time.sleep(10)  # プロセスが起動するまで待機する
        #    continue
 
        ## ソケットをクローズする
        #sock.close()

        # 10秒間隔でループを繰り返す
        time.sleep(10)

    # GPIOの後始末 
    #GPIO.cleanup()
    pi.stop()

# プロセスを起動する関数
def start_process():
    print(f"Process start : {ProcessName}")
    subprocess.Popen("./"+ProcessName)


def SendData(message):
    message = message.replace(' ', chr(0x1f))
    message += "\r\n"

    message = message.encode('utf-8')
    message = base64.b64encode(message)

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    client.connect((host, port))

    client.send(message)
    client.send("\n".encode('utf-8'))

    Result=False
    try:
       response = client.recv(4096)
    except socket.timeout:
       Result=False

    print("Response from command server :",response)
    if response == b'alive':
       Result=True

    client.close()

    return Result

def killall_Process():
    try:
        retcode = subprocess.check_call(['killall', ProcessName], shell=False)
    except subprocess.CalledProcessError as e:
        print(" Process kill failed.")

# ボタンが押された時に実行する関数
def button_pressed_callback(channel):
    print("Reset button pressed")
    WaitCount=20   # wait for 2 seconds 
    for i in range(WaitCount):
      time.sleep(0.1)
      #input_val = GPIO.input(BUTTON_PIN)
      input_val = pi.read(BUTTON_PIN)
      if (input_val==1):
          return
    print("Reset start")

    IfBreakDetected = True
    killall_Process()
    time.sleep(1)  # プロセスが終了するまで待機する
    start_process()
    time.sleep(10)  # プロセスが起動するまで待機する
    IfBreakDetected = False


def start_pigpio_daemon():
    # pigpiod デーモンが動作しているか確認
    try:
        pi = pigpio.pi()
        if not pi.connected:
            print("pigpioデーモンが動作していないため、起動します。")
            # デーモンを起動
            subprocess.run(["sudo", "pigpiod"], check=True)
            # 再度接続を試みる
            pi = pigpio.pi()
            if not pi.connected:
                raise RuntimeError("pigpioデーモンの起動に失敗しました。")
        else:
            print("pigpioデーモンは既に動作しています。")
        return pi
    except Exception as e:
        raise RuntimeError(f"pigpioデーモンの確認中にエラーが発生しました: {e}")

########################## MAIN #############################

if __name__ == "__main__":
        main()


###########################################################################
## 2023.
##   リリース
## 2024.5.20
##   PI.GPIOからpigpioへと変更
