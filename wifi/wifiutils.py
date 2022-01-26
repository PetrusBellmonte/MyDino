import subprocess, re, os
# TODO Make it clean!
# https://github.com/emlid/pywificontrol
# https://www.youtube.com/watch?v=hsm4poTWjMs
import time


def getCurrentSSID():
    devices = subprocess.check_output(['iwgetid', '-r'])
    if not devices:
        return None
    return devices.decode('ascii').strip()


'''def setWifi(ssid, password,prio=1):
    with open('/etc/wpa_supplicant/wpa_supplicant.conf') as f:
        file = f.read().split('\n')
    network = {}
    handled = False
    innet = False
    for i, line in enumerate(file):
        l = line
        if l == 'network={':
            network = {}
            innet = True
        elif l == '}' and innet:
            if network['ssid'][2] == ssid and 'psk' in network:
                handled = True
                i,ind,olpass = network['psk']
                file[i] = file[i][:ind]+password+file[i][ind+len(olpass):]
                if 'priority' in network:
                    i,ind,olpass = network['priority']
                    file[i] = file[i][:ind]+'0'+file[i][ind+len(olpass):]
                break
            print(network)
            innet = False
        elif innet:
            if l.strip().startswith('ssid'):
                l = l[l.index('ssid') + 4:].strip()
                l = l[l.index('=') + 1:].strip()
                if l.startswith('"'):
                    l = l[l.index('"') + 1:]
                    l = l[:l.index('"')]
                    network['ssid'] = (i, line.index(l,line.index('=')), l)
                else:
                    print(f'Cannot parse:', l.strip())
            elif l.strip().startswith('psk'):
                l = l[l.index('psk') + 3:].strip()
                l = l[l.index('=') + 1:].strip()
                if l.startswith('"'):
                    l = l[l.index('"') + 1:]
                    l = l[:l.index('"')]
                    network['psk'] = (i, line.index(l,line.index('=')), l)
                else:
                    print(f'Cannot parse:', l.strip())
            elif l.strip().startswith('priority'):
                l = l[l.index('=') + 1:].strip()
                if '#' in l:
                    l = l[:l.index('#')].strip()
                network['priority'] = (i, line.index(l,line.index('=')), l)
    if not handled:
        file.extend(['network={',
                     f'        ssid="{ssid}"',
                     f'        psk="{password}"',
                     f'        priority={prio}',
                     '}'])

    with open('/etc/wpa_supplicant/wpa_supplicant.conf', 'w') as f:
        f.write('\n'.join(file))'''

def validatePassword(password):
    assert len(password) >= 8, 'Password must be at least 8 chars long'
    assert len(password) <= 63, 'Password must not be longer than 63 chars'

def addWifi(ssid,password,prio=1,save = True):
    base = ['wpa_cli','-i','wlan0']
    validatePassword(password)
    print('Adding new Network...')
    i = subprocess.check_output([*base, 'add_network']).decode('ascii').strip()
    print('Setting ssid:')
    subprocess.call([*base,'set_network',i,'ssid',f'"{ssid}"'])
    print('Setting psk:')
    subprocess.call([*base,'set_network',i,'psk',f'"{password}"'])
    print('Setting prio:')
    subprocess.call([*base,'set_network',i,'priority','1'])
    print('Enabling network')
    subprocess.call([*base,'enable_network',i])
    if save:
        print('Save config')
        subprocess.call([*base,'save_config'])

def setWifi(ssid,password,prio=1,save=True):
    base = ['wpa_cli','-i','wlan0']
    validatePassword(password)
    print('Setting up Wifi:')
    print('List Networks:')
    networks = subprocess.check_output([*base, 'list_networks']).decode('ascii').strip().split('\n')[1:]
    networks = [x.split('\t') for x in networks]
    handled = False
    for i,ss,*rest in networks:
        if ssid==ss:
            print('Change psk of',ss)
            subprocess.call([*base,'set_network',i,'psk',f'"{password}"'])
            print('Change prio of',ss)
            subprocess.call([*base,'set_network',i,'priority','1'])
            handled = True
        else:
            print('Change prio of',ss)
            subprocess.call([*base,'set_network',i,'priority','0'])
    if not handled:
        addWifi(ssid,password,prio=prio,save=False)
    if save:
        print('Save Config')
        subprocess.call([*base,'save_config'])
    print(networks)

def prioritizeSSid(ssid, save=True):
    base = ['wpa_cli','-i','wlan0']
    print('Prioritize SSid',ssid)
    print('List Networks:')
    networks = subprocess.check_output([*base, 'list_networks']).decode('ascii').strip().split('\n')[1:]
    networks = [x.split('\t') for x in networks]
    for i,ss,*rest in networks:
        if ssid==ss:
            print('Change prio of',ss)
            subprocess.call([*base,'set_network',i,'priority','1'])
        else:
            print('Change prio of',ss)
            subprocess.call([*base,'set_network',i,'priority','0'])
    if save:
        print('Save Config')
        subprocess.call([*base,'save_config'])


def reloadWifi():
    subprocess.call(['wpa_cli','-i','wlan0','save_config'])

def availableNetwork():
    base = ['wpa_cli','-i','wlan0']
    subprocess.check_output([*base, 'scan'])
    time.sleep(0.1)
    networks = subprocess.check_output([*base, 'scan_results']).decode('ascii').strip().split('\n')[1:]
    return [x.split('\t') for x in networks]
