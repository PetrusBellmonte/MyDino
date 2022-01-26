import asyncio, os, subprocess
import time

from quart import Quart, render_template, request
from wifi.wifiutils import setWifi
from typing import Optional

app = Quart(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))


@app.route("/", methods=['POST', 'GET'])
async def hello_world():
    if request.method == 'POST':
        form = await request.form
        setWifi(form['ssid'], form['password'])
    return await render_template('dinoWifi.html')


mainTask: Optional[asyncio.Task] = None

stopTask: Optional[asyncio.Task] = None
stopTime= time.time()

async def stopAfter():
    while time.time()<stopTime:
        await asyncio.sleep(stopTime-time.time())
    await stop()


def start(timeout = 600):
    global mainTask,stopTask,stopTime
    if mainTask is None:
        subprocess.call(['systemctl', 'start', 'hostapd.service'])
        mainTask = asyncio.Task(app.run_task(host='0.0.0.0', port=80))
    if timeout is not None:
        stopTime = max(time.time()+timeout, stopTime)
    if stopTask is None:
        stopTask = asyncio.Task(stopAfter())


async def stop():
    global mainTask,stopTask
    print('STOPPING HOTSPOT!')
    # Kill Stop-task
    if stopTask is not None and not stopTask.done():
        stopTask.cancel()
    stopTask = None

    subprocess.call(['systemctl', 'stop', 'hostapd.service'])
    if mainTask is not None:
        mainTask.cancel()
        await asyncio.sleep(3)
        if not mainTask.done():
            print('WARNING: Quart was not finished properly.')
        mainTask = None

def cleanUp():
    asyncio.run(stop())
