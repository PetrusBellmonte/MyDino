import asyncio
import json
import websockets
from communication.server.clientManagement import CLIENTS
from communication.server.connectionManager import ConnectionManager


STATE = {"value": 0}


CONNECTIONS:ConnectionManager = ConnectionManager()

current_modus = None
current_state = True  # On
availableModes = {}
ADDRESS_ALL = 'ALL'
ADDRESS_OTHER = 'OTHERS'


async def notify(message, source=None, address = ADDRESS_OTHER):
    if address==ADDRESS_ALL:
        await notifyALL(message)
    elif address == ADDRESS_OTHER:
        await notifyOTHER(message,source=source)
    elif address.startswith('@'):
        webs = CONNECTIONS._typs.get(address[1:],[])
        if webs:
            await asyncio.wait([user.send(message) for user in webs])
    else:
        if address in CONNECTIONS._origins:
            CONNECTIONS._origins[address].send(message)
        elif source not in None:
            await source.send(json.dumps(error(f'Unknown address {address}')))

async def notifyALL(message, **kwargs):
    if CONNECTIONS:  # asyncio.wait doesn't accept an empty list
        print('>>', message)
        await asyncio.wait([user.send(message) for user in CONNECTIONS.websockets()])

async def notifyOTHER(message, source=None):
    if len(CONNECTIONS) > (source is not None):  # asyncio.wait doesn't accept an empty list
        print('>>', message)
        await asyncio.wait([user.send(message) for user in CONNECTIONS.websockets() if user != source])


def action(type, args, origin='server'):
    return {
        'type': type,
        'origin': origin,
        'args': args
    }


def error(message):
    return action('ERROR', {'message': message})


def introduction():
    return action('INTRODUCTION', {
        'name': 'server',
        'type': 'SERVER',
        'currentState': current_state,
        'currentMode': current_modus,
        'availableModes': CONNECTIONS.availableModes()
    })


def setMode(mode):
    return action('SET_MODE', mode)


def setState(state: bool):
    return action('SET_STATE', state)

async def handleIntroduction(websocket,data):
    global current_state, current_modus
    CONNECTIONS.init(websocket, data)

    intro = CONNECTIONS[websocket].intro
    # Update State & Mode if None is set
    if current_modus is None and 'currentMode' in intro and intro['currentMode'] is not None:
        current_modus = intro['currentMode']
        await notify(json.dumps(setMode(current_modus)), source=websocket)
    if current_state is None and 'currentState' in intro and intro['currentState'] is not None:
        current_state = intro['currentState']
        await notify(json.dumps(setState(current_state)), source=websocket)


async def sendIntroductions(websocket):
    await websocket.send(json.dumps(introduction()))
    for con in CONNECTIONS.values():
        if con.full_intro is not None:
            await websocket.send(json.dumps(con.full_intro))



async def handler(websocket: websockets.WebSocketServerProtocol, path):
    global current_modus, current_state
    CONNECTIONS.add(websocket)
    print(f'Handleing {len(CONNECTIONS)} connections after {websocket} joined.')
    await sendIntroductions(websocket)
    try:
        websocket_origin = None
        async for message in websocket:
            # Decode message
            print('<<',message)
            try:
                data = json.loads(message)
            except json.decoder.JSONDecodeError:
                await websocket.send(json.dumps(error('Invalid json')))
                continue
            # Check Networking
            # Check for origin
            origin = data.get('origin', None)
            if origin is None:
                await websocket.send(json.dumps(error('Origin must be set')))
                continue
            # TODO Sanitcheck
            # Check wether origin is right
            if websocket_origin is None:
                if data['origin'] in CONNECTIONS._origins:
                    await websocket.send(json.dumps(error('Bad origin: Origin already in use')))
                    await websocket.close()
                    continue
                websocket_origin = data['origin']
            elif websocket_origin != data['origin']:
                await websocket.send(json.dumps(error('Bad origin: Origin must be consistent with a websocket')))
                continue


            # Handle Data
            address = data.get('address',ADDRESS_OTHER)
            if 'type' not in data:
                await websocket.send(json.dumps(error('Could not identify type of action.')))
            elif 'args' not in data:
                print(data,'args' in data)
                await websocket.send(json.dumps(error('Could not identify args of action.')))
            elif data['type'] == 'SET_MODE':
                if 'newMode' in data['args']:
                    current_modus = data['args']['newMode']
                    await notify(message, source=websocket, address=address)
                else:
                    await websocket.send(json.dumps(error('Could not find the new mode.')))
            elif data['type'] == 'SET_STATE':
                if 'args' in data and 'newState' in data['args']:
                    current_state = data['args']['newState']
                    await notify(message, source=websocket, address=address)
                else:
                    await websocket.send(json.dumps(error('Could not find the new state.')))
            elif data['type'] == 'INTRODUCTION':
                await handleIntroduction(websocket,data)
                await notify(message, source=websocket, address=address)
            else:
                await notify(message, source=websocket, address=address)
                #await websocket.send(json.dumps(error('Unknown Action')))
    except websockets.ConnectionClosedError:
        pass
    finally:
        del CONNECTIONS[websocket]
    print(f'Handleing {len(CONNECTIONS)} connections after {websocket} left.')


async def process_request(path, request_header):
    if 'Sec-WebSocket-Protocol' not in request_header:
        return (404, {}, bytes())
    protocols = request_header['Sec-WebSocket-Protocol'].split(', ')
    if 'dino' in protocols:
        protocols.remove('dino')
    if len(protocols) != 1 or protocols[0] not in CLIENTS:
        return (404, {}, bytes())
    return None


start_server = websockets.serve(handler, "192.168.178.38", 6789, subprotocols=['dino',], process_request=process_request)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
