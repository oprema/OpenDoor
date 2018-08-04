#!/bin/bash

# Execute via sudo. Copy config files to /etc
sudo cp ./init.d/thin /etc/init.d
sudo cp ./init.d/nginx /etc/init.d
sudo cp ./thin/opendoor /etc/thin
sudo cp ./nginx/* /etc/nginx
sudo cp -R ./ssl/* /etc/ssl
sudo cp ./monit/conf.d/opendoorlog /etc/monit/conf.d
sudo cp ./logrotate.conf /etc
sudo cp ./rsyslog.conf /etc

# Create config files and directories
mkdir -p ~/app/log
chmod 777 ~/app/log
echo 'APP_PASS="passwd"' > ~/app/.env
sudo /usr/sbin/update-rc.d -f thin defaults

echo "Setup all done."
