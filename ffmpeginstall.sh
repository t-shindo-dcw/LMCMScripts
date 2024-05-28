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

sudo cp ~/lmc/libx264.so.138 /lib/arm-linux-gnueabihf/