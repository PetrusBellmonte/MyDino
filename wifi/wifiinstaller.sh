#!/bin/bash
if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi
echo ""
echo "--------------------------"
echo "Setting up Hotspot-Ability"
echo "--------------------------"

# Install stuff
echo "Installing libaries"
apt -y install dnsmasq hostapd

# Add Config
echo "Configuring dhcpcd"
cat << EOF >> /etc/dhcpcd.conf
interface ap@wlan0
static ip_address=192.168.1.1/24
nohook wpa_supplicant
EOF

echo "Extending dhcpcd.service"
cat > /etc/systemd/system/dhcpcd.service.d/override.conf <<EOF
[Service]
ExecStartPre=/sbin/iw dev wlan0 interface add ap@wlan0 type __ap
ExecStartPre=ifconfig ap@wlan0 192.168.1.1 netmask 255.255.255.0
ExecStopPost=/sbin/iw dev ap@wlan0 del
EOF

#Restart and add iterfaces
echo "Restart dhcpcd"
systemctl daemon-reload
systemctl restart dhcpcd

# DNSmasq
echo "Configuring DNSmasq"
mv /etc/dnsmasq.conf /etc/dnsmasq.conf_alt

cat > /etc/dnsmasq.conf <<EOF
# DHCP-Server aktiv für WLAN-Interface
interface=ap@wlan0

# DHCP-Server nicht aktiv für bestehendes Netzwerk
no-dhcp-interface=eth0
no-dhcp-interface=wlan0

# IPv4-Adressbereich und Lease-Time
dhcp-range=192.168.1.100,192.168.1.200,255.255.255.0,24h

# DNS
dhcp-option=option:dns-server,192.168.1.1
EOF

echo "Enable and restart dnsmasq"
systemctl restart dnsmasq
systemctl enable dnsmasq

# hostapd
echo "Writing hostapd"
cat > /etc/hostapd/hostapd.conf <<EOF
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
EOF

chmod 600 /etc/hostapd/hostapd.conf

echo "UnMasking hostapd"
systemctl unmask hostapd
#systemctl start hostapd


#Cleaning Up
echo "Disabling wpa_supplicant second service"
systemctl stop wpa_supplicant.service
systemctl disable wpa_supplicant.service