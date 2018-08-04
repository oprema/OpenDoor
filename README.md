# OpenDoor a Raspberry Pi Application to open doors in an apartment building.

For some people it is simply convinient to open the apartment door via a web application. Some reasons may be: Lots of visitors to a certain time (let them all in if needed), being handicapped (no need to go to the door to open it) or simply being lazy :-).

### Hardware

The best use case for OpenDoor exists of a front door that is controlled by a intercom system (in my case a Siedle HTA 811-0W) and the door to the apartment. OpenDoor is able to open both doors through a Raspi Zero that is connected to the Siedle. An electromechanical door opener controls the apartment door and does the Voodoo (Hörmann PortaMatic).

### How does it work?

Most likely you have a different hardware setup. To make OpenDoor to work with it, you must provide 3 functions:

1. On one of the Raspi GPIO inputs you must detect doorbell ringing
2. One GPIO output controls the relais for the front door (release buzzer for 5 sec)
3. The other GPIO output controls the relais for the apatment door (parallel to the door opener switch)

### Features of OpenDoor

1. Open front or apartment door through a Web Interface
2. HTTPS-WebServer with basic Authentication for the Web Interface
3. User dependent authorizations for API usage
4. Weekly time based open actions when someone rings the bell
5. Web notifications when the door bell rings
6. Logging ringing and who opened which door at a time
7. English and German language support

### Technology used

- Nginx Web server as a reverse proxy for the used Thin application server
- A Sinatra app using Ruby and Thin with Web-Sockets for notifications
- Haml and Javascript for the Web-Front-End
- SQLite3 for persistent data storage
- A Python-GPIO program using Unix IPC (pipes) to communicate with the
  Thin application server

## Installing OpenDoor on a Raspberry Pi Zero (Raspbian Stretch Lite - 2018-06-27)

Programm your SD-Card (Etcher) and setup a headless configuration so you can use
ssh over WLan. Get an internet connection and

Update your Raspbian with
```
sudo apt-get update
sudo apt-get upgrade
```
Install Git with
```
sudo apt-get install git
```
Checkout OpenDoor directly into /home/pi and create the directory below
```
mkdir ~/.opendoord
sudo chmod -R 775 ~/.opendoord
```
Next install a recent Ruby 2.5.1 (.rbenv) with ~/.ruby_install.sh (not sudo)
This takes about 2h on a raspi zero!
Next we need more Raspbian and Python3 packages
```
sudo apt-get install python3-pip python3-dev monit libsqlite3-dev
sudo pip3 install setproctitle docopt pytz
```
Change directory to ~/etc and execute the following script to add monit, startup-skripts, SSL-Certs etc.
```
./setup.sh
```

### Install the used Gems (Thin, Sinatra, SQLite and more)

The Ruby app makes usage of several Gems which need to be installed.
Execute the following commands:
```
cd ~/app
gem install bundler
bundle install
```
#### Define your Basic Auth password
```
vi ~/app/.env
```
replace passwd and use your own
```
APP_PASS="passwd"
```

### WLan gets bored and falls asleep

I am using a Raspi-Zero (1st Generatiom) without build-in WLan.
Instead, I connected an Edimax WLan-Adapter (Chipset: Realtek) to the
Mico-USB.

I noticed after several hours of idleing that the WLan turned it self off and got unresponsive for up-to 30 secs (not great if you want to open the door imediately while you have someone waiting).

#### Turning off WLan Power saving mode

First check if you have a similar WLan adapter in use:
```
lsmod
```
if you see a module named "8192cu" you might turn off the power saving mode,
but first check if power saving is on.
```
iw wlan0 get power_save
```
If it says "Power save: on" then turn it off
```
sudo vi /etc/modprobe.d/8192cu.conf
```
by adding the following line
```
options 8192cu rtw_power_mgnt=0 rtw_enusbss=0
```
afterwards execute a reboot
```
sudo reboot
```
and check again with
```
iw wlan0 get power_save
```
It should be off now.

### Finally
Add two entries to the crontab for the user pi:
```
crontab -e
```
add:
```
@reboot sudo rm /tmp/*fifo
@reboot sudo ~/opendoord.py --verbose
```

### Do not forget to change the default pi password.
