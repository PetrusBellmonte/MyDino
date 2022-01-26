import asyncio
import threading

from lightcontroll.mode import Mode
from threading import Thread, Event
from typing import Optional
import time

from lightcontroll.neoPixel import DisconnectedNeoPixel

class ModeSimulation:
    def __init__(self, mode: Mode, manager=None):
        super().__init__()
        self._loop = asyncio.get_event_loop()
        self.mode = mode
        self.manager: ModeSimulationManager = manager
        self.thread_stop_event: Optional[Event] = threading.Event()
        self.thread: Optional[Thread] = None
        self.run_until_origin = {}
        self.origin_callback = {}
        # Autostart
        self.start()

    def __setitem__(self, key, value):
        self.run_until_origin[key] = time.time()+5
        self.origin_callback[key] = value

    async def trigger(self, board:DisconnectedNeoPixel):
        if self.origin_callback:
            await asyncio.gather([callback(board) for callback in self.origin_callback.values()])

    @property
    def run_until(self):
        return max(self.run_until_origin.values(),default=time.time())
    @property
    def run_next(self):
        return min(self.run_until_origin.values(),default=time.time())


    def enlong(self, origin, t=5):
        if origin in self.run_until_origin:
            self.run_until_origin[origin] = max(self.run_until_origin[origin], time.time() + t)

    def start(self):
        if self.thread is not None:
            self.thread_stop_event.set()
            self.thread.join()
            self.thread_stop_event.clear()
            self.mode_thread = None
        class MyNeoPix(DisconnectedNeoPixel):
            def _transmit(self_board, buffer: bytearray) -> None:
                asyncio.run_coroutine_threadsafe(self.trigger(self_board), self._loop)

        self.thread = Thread(target=self.mode.execute, args=(self.thread_stop_event, MyNeoPix(58)))
        self.thread.start()
        asyncio.Task(self.awaitStop())

    async def awaitStop(self):
        await asyncio.sleep(5)
        while len(self.run_until_origin) and time.time() < self.run_until:
            for origin, tm in self.run_until_origin.items():
                if tm<=time.time():
                    del self.run_until_origin[origin]
                    del self.origin_callback[origin]
            if len(self.run_until_origin):
                break
            await asyncio.sleep(self.run_next - time.time())
        self.stop()

    def stop(self):
        self.run_until_origin.clear()
        self.origin_callback.clear()
        if not self.thread_stop_event.is_set():
            self.thread_stop_event.set()
        self.thread.join()
        if self.manager is not None:
            self.manager.remove(self.mode)


class ModeSimulationManager(dict):

    def getOrCreate(self,mode):
        if mode not in self:
            self.add(mode)
        return self[mode]

    def add(self, mode):
        super().__setitem__(mode, ModeSimulation(mode, manager=self))

    def __setitem__(self, key, value):
        assert isinstance(key, Mode)
        assert isinstance(value, ModeSimulation)
        super().__setitem__(key, value)

    def __delitem__(self, key):
        self[key].stop()

    def remove(self, mode):
        super().__delitem__(mode)

    def stopAll(self):
        for ms in list(self.values()):
            ms.stop()
