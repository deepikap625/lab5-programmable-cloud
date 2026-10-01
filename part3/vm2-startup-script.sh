#!/bin/bash

apt-get update
apt-get install -y python3 python3-pip git

cd /home
git clone https://github.com/cu-csci-4253-datacenter/flask-tutorial

cd flask-tutorial
sudo pip3 install .
sudo python3 -m flask --app flaskr init-db
sudo nohup python3 -m flask --app flaskr run --host=0.0.0.0 >/tmp/flask.log 2>&1 &
