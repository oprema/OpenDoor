#!/bin/sh

COMMAND='sudo /home/pi/opendoord.py --verbose'
LOGFILE=restart-opendoor.txt

writelog() {
  now=`date`
  echo "$now $*" >> $LOGFILE
}

rm $LOGFILE
writelog "Starting"
sudo rm /tmp/*fifo
while true ; do
  $COMMAND
  writelog "Exited with status $?"
  writelog "Restarting"
done
