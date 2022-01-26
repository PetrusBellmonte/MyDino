#!/bin/bash

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

# Set CDW
parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
cd "$parent_path" || exit

echo "Updating pi"
apt-get update
apt-get upgrade -y

bash wifi/wifiinstaller.sh

echo "Installing pip3"
apt-get -y install python3-pip

echo "Installing Python libaries"
pip3 install --upgrade setuptools
pip3 install adafruit-circuitpython-neopixel pyyaml websockets adafruit-circuitpython-fancyled quart

cp "./configs/example-dino.yml" "./configs/dino.yml"

read -p "Configure yml? " -n 1 -r
echo    # (optional) move to a new line
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "Editing Config"
    python3 setupConfig.py
fi

# Activate Dino
cp services/dinoclient.service /etc/systemd/system
systemctl daemon-reload
systemctl enable dinoclient.service
systemctl start dinoclient.service