from __future__ import annotations

import traceback, string, random
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from controller import LightController
import asyncio, json
import websockets

from lightcontroll.mode import Mode
from configs.dinoconf import Config
from communication.client.modesimulation import ModeSimulationManager

if 'websocket' not in Config:
    print('Configuration for websocket is missing...')
    key = input('Websocket-Key: ')
    uri = input('Websocket-URI: ')
    Config['websocket'] = {'KEY': key, 'URI': uri}
    del key
    del uri


class Dinoclient:
    def __init__(self, lc: LightController, name, uri, key, origin=None):
        self.lc = lc
        self.name = name
        self.uri = uri
        self.key = key
        self.dinosocket: websockets.WebSocketClientProtocol = None
        self.origin = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(20)) if origin is None else origin
        self.simlator: ModeSimulationManager = ModeSimulationManager()

        # asyncio
        self.task: Optional[asyncio.Task] = None

    def action(self, typ, args, address='OTHERS'):
        return {
            'type': typ,
            'origin': self.origin,
            'address': address,
            'args': args
        }

    async def send(self, data):
        if self.dinosocket is not None:
            await self.dinosocket.send(json.dumps(data))
            print('>>', json.dumps(data))
            return True
        return False

    async def sendSetMode(self, mode: Mode):
        await self.send(self.action('SET_MODE', {'newMode': mode.json()}))

    async def sendSetState(self, state: bool):
        await self.send(self.action('SET_STATE', {'newState': state}))

    async def run_retry_client(self, timeout=10, catchCancle=True):
        try:
            while True:
                await self.run_client(catchCancle=False)
                await asyncio.sleep(timeout)
        except asyncio.CancelledError:
            if not catchCancle:
                print('run_retry_client canceled')
                raise
            pass

    async def run_client(self, catchCancle=True):
        print('Attempt Connect')
        try:
            self.dinosocket = await websockets.connect(self.uri, subprotocols=['dino', self.key])
        except (websockets.InvalidStatusCode, websockets.ConnectionClosedError, TimeoutError):
            print('No Connection possible')
            return
        print('Connected')
        await self.send({
            "type": "INTRODUCTION",
            "origin": self.origin,
            "args": {
                "name": "Simons Dino",
                "type": self.name,
                "currentState": self.lc.state,
                "currentMode": None if self.lc.current_mode is None else self.lc.current_mode.json(),
                "possibleModes": [m().json() for m in Mode.MODES.values()],  # Offered by the device
            }
        })
        try:
            while True:
                print('Wait for data')
                data = await self.dinosocket.recv()
                data = json.loads(data)
                print(f'<< {data}')
                if 'type' not in data or 'args' not in data:
                    continue
                elif data['type'] == 'INTRODUCTION' and 'type' in data['args'] and data['args']['type'] == 'SERVER':
                    if data['args']['currentMode'] is not None:
                        print(data['args']['currentMode'])
                        self.lc.setMode(Mode.fromJson(data['args']['currentMode']), False)
                    if data['args']['currentState'] is not None:
                        self.lc.state = data['args']['currentState'], False
                elif data['type'] == 'SET_MODE':
                    if 'newMode' not in data['args']:
                        continue
                    mode = Mode.fromJson(data['args']['newMode'])
                    self.lc.setMode(mode, broadcast=False)
                elif data['type'] == 'SET_STATE':
                    self.lc.state = data['args']['newState'], False
                elif data['type'] == 'PREVIEW_ABILITY':
                    if data['type']['args']['type'] == 'REQUEST' and data['type']['args']['mode']['type'] in Mode.MODES:
                        await self.send(self.action('PREVIEW_ABILITY', {'mode': data['type']['args']['mode'], 'type': 'REPLY'}, address=data['origin']))
                elif data['type'] == 'REQUEST_PREVIEW':
                    if data['type']['args']['mode']['type'] not in Mode.MODES:  # TODO Send Error
                        pass
                    else:
                        def callBackGen(origin, mode):
                            async def callback(pixB):
                                await self.send(self.action('STREAM', {'data': list(pixB), 'mode': mode}, address=origin))

                            return callback

                        self.simlator.getOrCreate(data['type']['args']['mode'])[data['origin']] = callBackGen(data['origin'], data['type']['args']['mode'])


        except asyncio.CancelledError:
            if not catchCancle:
                print('run_client canceled')
                raise
        except websockets.ConnectionClosedError:
            print('Connection Closed')
            traceback.print_exc()
            pass
        except Exception as a:
            print('WPAAAAAT??????')
            print(a)
            print('---')
            traceback.print_exc()
            raise a
        finally:
            await self.dinosocket.close()
            self.dinosocket = None

    @property
    def running(self):
        return self.task is not None and not self.task.done()

    def start(self, retry=True):
        # Kill if running
        if self.task is not None:
            self.stop()

        # Start Task
        if retry:
            self.task = asyncio.Task(self.run_retry_client())
        else:
            self.task = asyncio.Task(self.run_client())

    def restartIfRunning(self):
        if self.task is not None:
            self.start()

    def stop(self):
        if self.running:
            self.task.cancel()
        self.task = None

    def cleanUp(self):
        self.stop()
        self.simlator.stopAll()


class ConfigDinoclient(Dinoclient):
    def __init__(self, lc: LightController):
        super().__init__(lc, None, None, None)
        Config['websocket'].addOnChangeListener(self.configlistener)

    def configlistener(self, path, value, **kwargs):
        self.restartIfRunning()

    @property
    def name(self):
        return Config['websocket']['name']

    @name.setter
    def name(self, val):
        if val is not None:
            print('WARNING: Attempt to set name')

    @property
    def uri(self):
        return Config['websocket']['URI']

    @uri.setter
    def uri(self, val):
        if val is not None:
            print('WARNING: Attempt to set URI')

    @property
    def key(self):
        return Config['websocket']['KEY']

    @key.setter
    def key(self, val):
        if val is not None:
            print('WARNING: Attempt to set KEY')

    def __del__(self):
        Config['websocket'].removeOnChangeListener(self.configlistener)
