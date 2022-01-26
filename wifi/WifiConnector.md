## Utils
#### Get IPs
```bash
hostname -I
```

####Get current SSID
```bash
iwgetid -r
```

## Setup better access-point-ability
This one is mostly based on [-](https://www.elektronik-kompendium.de/sites/raspberry-pi/2002171.htm)

### Install Libaries
```bash
sudo apt install dnsmasq hostapd
```

### Setup dhcpcd
Add the following to the end of `/etc/dhcpcd.conf`
```
interface ap@wlan0
static ip_address=192.168.1.1/24
nohook wpa_supplicant
```
Extend the *Service* BLock of ``/lib/systemd/system/dhcpcd.service``
```editorconfig
[Service]
ExecStartPre=/sbin/iw dev wlan0 interface add ap@wlan0 type __ap
ExecStartPre=ifconfig ap@wlan0 192.168.1.1 netmask 255.255.255.0
ExecStopPost=/sbin/iw dev ap@wlan0 del
```
And restart the service: 
````
sudo systemctl daemon-reload
sudo systemctl restart dhcpcd
````

### Set up dnsmasq

Backup old conf (optional):
``sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf_alt``

Edit ``/etc/dnsmasq.conf``:
```
# DHCP-Server aktiv für WLAN-Interface
interface=ap@wlan0

# DHCP-Server nicht aktiv für bestehendes Netzwerk
no-dhcp-interface=eth0
no-dhcp-interface=wlan0

# IPv4-Adressbereich und Lease-Time
dhcp-range=192.168.1.100,192.168.1.200,255.255.255.0,24h

# DNS
dhcp-option=option:dns-server,192.168.1.1
```
Restart dnsmasq and enable if not already:
````bash
sudo systemctl restart dnsmasq
sudo systemctl enable dnsmasq
````

###Setup hostapd
Configure ``/etc/hostapd/hostapd.conf``:
```
# WLAN-Router-Betrieb

# Schnittstelle und Treiber
interface=ap@wlan0
#driver=nl80211

# WLAN-Konfiguration
ssid=WLANrouter
channel=1
hw_mode=g
ieee80211n=1
ieee80211d=1
country_code=DE
wmm_enabled=1

# WLAN-Verschlüsselung
auth_algs=1
wpa=2
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
wpa_passphrase=testtest
```
Change Permission so that it can be read by the hostapd:
```
sudo chmod 600 /etc/hostapd/hostapd.conf
```
Uncover Service for hostapd:
```
sudo systemctl unmask hostapd
sudo systemctl start hostapd
```

###Cleanup
The dns-stuff does not realy work, sooooo WORKAROUND... Put ``192.168.1.1    dinoconfig`` in ``/etc/hosts``.

Ther are to many WPA-Services: Just turn one off :D
```bash
sudo systemctl stop wpa_supplicant.service
sudo systemctl disable wpa_supplicant.service
```

## wpa_cli
With ``sudo wpa_cli -i wlan0``:

### Save Changes to file & update
[Source](https://raspberrypi.stackexchange.com/questions/73749/how-to-connect-to-wifi-without-reboot)
```bash
save_config # Save changes
reconfigure # Reload file and reestablish connections
```
### List known network
```bash
list_networks
```
### List detected network
```bash
scan
scan_results
```

### Add Network
[Source](https://unix.stackexchange.com/questions/415816/i-am-trying-to-connect-to-wifi-using-wpa-cli-set-network-command-but-it-always-r)
```bash
scan
scan_results
add_network # Returns an id/number
set_network <id> ssid "<SSID>"
set_network <id> psk "<Password>"
set_network <id> priority 0 # Default prio for this project
enable_network <id>
save_config # Save changes
```
### Connect to network
```bash
set_network <id> priority 1 #Set to highest Prio. Probably should not be saved
reassociate # Connect again using new prio
```









## Setup access-point-ability#
This is mostly copied from [Stackoverflow](https://raspberrypi.stackexchange.com/questions/89803/access-point-as-wifi-router-repeater-optional-with-bridge)

### Install hostapd for the access point
```bash
sudo apt install hostapd
```

Make a file */etc/hostapd/hostapd.conf*:
```
driver=nl80211
ssid=RPiNet
country_code=DE
hw_mode=g
channel=1
auth_algs=1
wpa=2
wpa_passphrase=verySecretPassword
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
```
and change permissions:
```bash
sudo chmod 600 /etc/hostapd/hostapd.conf
```
Add Service:
```bash
sudo systemctl edit --force --full accesspoint@.service
```
with the following content:
```editorconfig
[Unit]
Description=accesspoint with hostapd (interface-specific version)
Wants=wpa_supplicant@%i.service

[Service]
ExecStartPre=/sbin/iw dev %i interface add ap@%i type __ap
ExecStart=/usr/sbin/hostapd -i ap@%i /etc/hostapd/hostapd.conf
ExecStopPost=-/sbin/iw dev ap@%i del

[Install]
WantedBy=sys-subsystem-net-devices-%i.device
```

### Setup wpa_supplicant for client connection
Add the following to file */etc/wpa_supplicant/wpa_supplicant-wlan0.conf*:
```
country=DE
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
    ssid="MyRealWLAN"
    psk="realyNotMyPassword"
    key_mgmt=WPA-PSK   # see ref (4)
}
```
Adjust permissions and disable default service:
```bash
sudo chmod 600 /etc/wpa_supplicant/wpa_supplicant-wlan0.conf
sudo systemctl disable wpa_supplicant.service
```
Add service with ``sudo systemctl edit wpa_supplicant@wlan0.service```:
```editorconfig
[Unit]
BindsTo=accesspoint@%i.service
After=accesspoint@%i.service
```
### Setup static interfaces
Add file */etc/systemd/network/08-wifi.network*:
```editorconfig
[Match]
Name=wl*
[Network]
LLMNR=no
MulticastDNS=yes
# If you need a static ip address, then toggle commenting next four lines (example)
DHCP=yes
#Address=192.168.50.60/24
#Gateway=192.168.50.1
#DNS=84.200.69.80 1.1.1.1
```