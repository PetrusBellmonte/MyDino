#My Dino

This repo contains the code for a Dino

## Client Installation

> :warning: ⚠️ All commands have to be executed as root. So do all installtions as root.

There is a setup script:

Otherwise T

### Manual Installation

This mthod is mostly based on [adafruit](https://learn.adafruit.com/circuitpython-on-raspberrypi-linux/installing-circuitpython-on-raspberry-pi).

#### Prepare for neopixel
```bash
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install python3-pip -y
sudo pip3 install --upgrade setuptools
```
#### Install libaries
```bash
sudo pip3 install adafruit-circuitpython-neopixel pyyaml websockets adafruit-circuitpython-fancyled quart
```

#### Setup Hostpot-Ability
```bash
sudo bash wifi/wifiinstaller.sh
```
#### Fill in dino-config
```bash
cp "./config/example-dino.yml" "./config/dino.yml"
sudo python3 setupConfig.py
```


#### Put Client in Place:
```bash
sudo cp services/dinoclient.service /etc/systemd/system
sudo systemctl daemon-reload # Reload to find new files and notice changes
sudo systemctl enable dinoclient.service # Start when booted up
sudo systemctl start dinoclient.service # Start service
```