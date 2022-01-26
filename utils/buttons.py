import RPi.GPIO as GPIO
import asyncio, time, threading
from typing import Optional

GPIO.setwarnings(False)  # Ignore warning for now
GPIO.setmode(GPIO.BCM)  # Use physical pin numbering

_loop = asyncio.get_event_loop()

_onEvents = {}

_listeners = lambda: {'onClick': [], 'onHold': [], 'onPress': []}

isRunning = threading.Event()

pins = []
lastPinState = {}
lastChangeTime = {}
lastHoldTime = {}
steps = {}

minHoldDelta = 0.3
holddelta = minHoldDelta


def changeListener(stopEvent: threading.Event):
    lastChangeTime = time.time()
    lastHoldTime = time.time()
    lastState = None
    steps = 0
    while not stopEvent.wait(0.002):
        key = tuple(sorted(pin for pin in pins if GPIO.input(pin)))
        now = time.time()
        if key != lastState:
            if lastState in _onEvents and len(key)<len(lastState):
                delta = now - lastChangeTime
                for f in _onEvents[lastState]['onClick']:
                    _loop.call_soon_threadsafe(lambda: _loop.create_task(f(steps=steps, delta_time=delta, total_time=delta, key=key, typ='onClick')))

            lastState = key
            lastChangeTime = now
            lastHoldTime = now
            steps = 0

            if key in _onEvents:
                for f in _onEvents[key]['onPress']:
                    _loop.call_soon_threadsafe(lambda: _loop.create_task(f(steps=steps, delta_time=now - lastHoldTime, total_time=now - lastChangeTime, key=key, typ='onPress')))

        else:
            if now-lastHoldTime>=minHoldDelta:
                if key in _onEvents:
                    for f in _onEvents[key]['onHold']:
                        _loop.call_soon_threadsafe(lambda: _loop.create_task(f(steps=steps, delta_time=now - lastHoldTime, total_time=now - lastChangeTime, key=key, typ='onHold')))

                lastHoldTime = now
                steps += 1



def onClick(*pins, func=None):
    def deco(f):
        for pin in pins:
            if pin not in _onEvents:
                _initPin(pin)
        key = tuple(sorted(pins))
        _initKey(key)
        _onEvents[key]['onClick'].append(f)
        return f

    if func is not None:
        return deco(func)
    return deco


def onHold(*pins, func=None):
    def deco(f):
        for pin in pins:
            if pin not in pins:
                _initPin(pin)
        key = tuple(sorted(pins))
        _initKey(key)
        _onEvents[key]['onHold'].append(f)
        return f

    if func is not None:
        return deco(func)
    return deco

def onPress(*pins, func=None):
    def deco(f):
        for pin in pins:
            if pin not in pins:
                _initPin(pin)
        key = tuple(sorted(pins))
        _initKey(key)
        _onEvents[key]['onPress'].append(f)
        return f

    if func is not None:
        return deco(func)
    return deco


def _initPin(pin):
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  # Set pin 10 to be an input pin and set initial value to be pulled low (off)
    lastPinState[pin] = GPIO.input(pin)
    pins.append(pin)

def _initKey(key):
    if key not in _onEvents:
        _onEvents[key] = _listeners()


def cleanUp():
    isRunning.set()
    listenerThread.join()
    GPIO.cleanup()


listenerThread = threading.Thread(target=changeListener, args=(isRunning,))
listenerThread.start()
