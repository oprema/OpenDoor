#!/bin/bash
# execute with sudo. Copy files from /etc
cp /etc/init.d/thin ./init.d
cp /etc/init.d/nginx ./init.d
cp /etc/thin/opendoor ./thin
cp /etc/nginx/nginx.conf ./nginx
cp /etc/logrotate.conf .
