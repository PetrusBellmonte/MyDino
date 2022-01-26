from __future__ import annotations
from typing import List, Optional
from lightcontroll.mode import Mode
from configs.dinoconf import Config
from communication.client.dinoclient import ConfigDinoclient,Dinoclient
from lightcontroll.modes import defaultmodes,rainbowmodes
from utils import buttons as button
from wifi import WifiConnect
import threading, asyncio
import board
import neopixel


class LightController:
    LIGHT_CONTROLLER = None

    def __init__(self, modes: List[Mode]):
        if self.LIGHT_CONTROLLER is not None:
            raise Exception('A light-controller is already running.')
        self.LIGHT_CONTROLLER = self
        self.dc: Optional[Dinoclient] = ConfigDinoclient(self)
        self.neoPix = neopixel.NeoPixel(board.D18, Config['lightcontroll']['pixels'], brightness=1.0, auto_write=False, pixel_order=neopixel.GRB)

        self.modes = modes

        # Mode running
        self.mode_thread: Optional[threading.Thread] = None
        self.thread_stop_event: threading.Event = threading.Event()
        self.current_mode: Mode = Mode.fromJson(Config['lightcontroll']['currentmode']) if 'currentmode' in Config['lightcontroll'] else None
        self.updateModeThread()

        # Listener
        self.onModeChangeListeners = []
        self.onStateChangeListeners = []

        # INit
        self.updateDinoCLient()

    @classmethod
    def getInstance(cls):
        if cls.LIGHT_CONTROLLER is None:
            LightController([])
        return cls.LIGHT_CONTROLLER

    @property
    def state(self):
        return Config['lightcontroll'].get('state', True)

    @state.setter
    def state(self, value):
        # Unpack Value
        if isinstance(value, (list, tuple)):
            value, broadcast = value
        else:
            broadcast = True
        # Only change if real change
        if value == Config['lightcontroll'].get('state', True):
            return
        # Activate Dino if not yet
        if not self.superstate and value:
            self.superstate = True
        # Set Value
        Config['lightcontroll']['state'] = value
        # Broadcast
        if broadcast and self.dc is not None:
            asyncio.Task(self.dc.sendSetState(value))
        # Update Mode
        self.updateModeThread()
        for listener in self.onStateChangeListeners:
            listener(value)

    @property
    def superstate(self):
        return Config['lightcontroll'].get('superstate', True)

    @superstate.setter
    def superstate(self, value):
        if Config['lightcontroll'].get('superstate', True) == value:
            return
        Config['lightcontroll']['superstate'] = value
        self.updateDinoCLient()
        if not value and self.state:
            self.state = False

    @property
    def brightness(self):
        return Config['lightcontroll'].get('brightness', 1.0)

    @brightness.setter
    def brightness(self, value):
        Config['lightcontroll']['brightness'] = max(0.0, min(1.0, value))

    def setMode(self, mode: Mode, broadcast=True):
        print('setMode', mode)
        if self.current_mode == mode:
            return
        # Set new Mode
        self.current_mode = mode
        # Broadcast
        if broadcast:
            asyncio.Task(self.dc.sendSetMode(mode))
        # Update modethread
        self.updateModeThread()

        # Trigger listener
        Config['lightcontroll']['currentmode'] = mode.json()
        for listener in self.onModeChangeListeners:
            listener(mode)

    def updateModeThread(self):
        # Stop old Mode
        if self.mode_thread is not None:
            self.thread_stop_event.set()
            self.mode_thread.join()
            self.thread_stop_event.clear()
            self.mode_thread = None
        if self.current_mode is not None and self.state:
            self.mode_thread = threading.Thread(target=self.current_mode.execute, args=(self.thread_stop_event,self.neoPix))
            self.mode_thread.start()
        else:
            self.neoPix.fill((0, 0, 0))
            self.neoPix.show()

    def nextMode(self):
        if self.current_mode is None or self.current_mode not in self.modes:
            if self.modes:
                self.setMode(self.modes[0])
        else:
            self.setMode(self.modes[(self.modes.index(self.current_mode) + 1) % len(self.modes)])

    def updateDinoCLient(self):
        if Config['lightcontroll']['superstate']:
            if not self.dc.running:
                self.dc.start()
        else:
            if self.dc.running:
                self.dc.stop()
    def cleanUp(self):
        self.dc.stop()
        if self.thread_stop_event is not None:
            self.thread_stop_event.set()
        if self.mode_thread is not None:
            self.mode_thread.join()



loop = asyncio.get_event_loop()
lc = LightController([Mode.fromJson(m) for m in Config['lightcontroll']['modes']])



###############################
#       Button-Controll       #
###############################
@button.onClick(Config['buttons']['mode'])
async def click_mode(delta_time=None, **kwargs):
    if not lc.state:
        return
    print('Change Mode')
    lc.nextMode()


@button.onClick(Config['buttons']['power'])
async def click_power(delta_time=None, **kwargs):
    if delta_time >= Config['buttons']['superstatetime']:
        return
    print('Change State')
    lc.state = not lc.state


@button.onHold(Config['buttons']['power'])
async def hold_power(delta_time=None, **kwargs):
    if delta_time < Config['buttons']['superstatetime']:
        return
    if lc.superstate:
        print('Change Superstate')
        lc.superstate = False


@button.onClick(Config['buttons']['minus'])
async def click_minus(delta_time=None, **kwargs):
    if delta_time >= Config['buttons']['holdtime']:
        return
    print('Decrease Brightness')
    lc.brightness -= 0.05


@button.onHold(Config['buttons']['minus'])
async def hold_minus(delta_time=None, **kwargs):
    if delta_time < Config['buttons']['holdtime']:
        return
    print('Decrease Brightness by', 0.2 * button.holddelta)
    lc.brightness -= 0.2 * button.holddelta


@button.onClick(Config['buttons']['plus'])
async def click_plus(delta_time=None, **kwargs):
    if delta_time >= Config['buttons']['holdtime']:
        return
    print('Increase Brightness')
    lc.brightness += 0.05


@button.onHold(Config['buttons']['plus'])
async def hold_plus(delta_time=None, **kwargs):
    if delta_time < Config['buttons']['holdtime']:
        return
    print('Increase Brightness by', 0.2 * button.holddelta)
    lc.brightness += 0.2 * button.holddelta

@button.onPress(Config['buttons']['power'],Config['buttons']['plus'])
async def start_hotspot(**kwargs):
    print('START HOTSPOT!!!!')
    WifiConnect.start()


if __name__ == '__main__':
    try:
        loop.run_forever()
        print('Finished running forever')
    except KeyboardInterrupt:
        lc.cleanUp()
        button.cleanUp()
        WifiConnect.cleanUp()
