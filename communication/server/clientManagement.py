import json,os,random,string

CLIENTFILE = os.path.join(os.path.dirname(os.path.realpath(__file__)),'clients.db')
CHARS = string.digits+string.ascii_letters
CLIENTS = {}
if os.path.exists(CLIENTFILE):
    with open(CLIENTFILE) as f:
        CLIENTS = json.loads(f.read())

def addClient(name = None, should_print = None, save_file=None):
    name = input('Clientname') if name is None else name
    key = '-'.join(''.join(random.choice(CHARS) for __ in range(5)) for _ in range(5))
    CLIENTS[key] = {'name':name}
    saveCLients()

    print('Key added...')
    if should_print is None:
        resp = input('Print Key? (Yes)')
        if resp.lower() in ['','y','yes']:
            print('Key:\n'+key)
    elif should_print:
        print('Key:\n'+key)

    if save_file is None:
        resp = input('Save as file? (Yes)')
        if resp.lower() in ['','y','yes']:
            resp = input(f'Choose Filename? ("{name}.key")')
            if resp !='':
                with open('resp','w') as f:
                    f.write(key)
    elif save_file:
        with open(save_file, 'w') as f:
            f.write(key)
    return key

def saveCLients():
    with open(CLIENTFILE,'w') as f:
        f.write(json.dumps(CLIENTS))

