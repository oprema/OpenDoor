# OpenDoor
### A Raspberry Pi Application to open doors in an appartment house.
For some people it is simply convinient to open the appartment doors via a 
web application or based on time or via a mobile app. 

### Technology used:
Nginx server, Thin application server (Web-Sockets for notifications), A Python-GPIO app
to communicate with the application server via fifos.

### Hardare:
Here in Germany an appartment house exists of an entrance door that is controlled by a door
intercom system and the door to the flat. OpenDoor is able to open both doors through a Raspi Zero
that is connected to a Siedle (Siedle HTA 811-0W) and a Hörmann (PortaMatic).

### Installation of OpenDoor on a Raspberry Pi Zero (Raspbian Lite 4.9.2-10)
Setup your SD-Card and expand it to use all of its capacity.
Get an internet connection and update your Raspbian with:
```
sudo apt-get update
sudo apt-get upgrade
```
Install Git with
```
sudo apt-get install git
```
Checkout OpenDoor

Next install a recent Ruby 2.3.1 (.rbenv) with ~/.ruby_install.sh (not sudo)
This takes about 2h on a raspi zero!
```
sudo apt-get install python-pip python-dev monit
sudo pip install setproctitle docopt pytz
```
change directory to ~/etc and execute
```
./setup.sh
```
Add two entries to the crontab of the user pi:
```
crontab -e
```
```
@reboot sudo rm /tmp/*fifo
@reboot sudo ~/opendoord.py --verbose
```
### Save power:
add in /etc/rc.local to disable HDMI on boot:
```
/usr/bin/tvservice -o
```
#### Disable the ACT LED on the Pi Zero.
add in /boot/config.txt:
```
dtparam=act_led_trigger=none
dtparam=act_led_activelow=on
```

# Code coming soon
