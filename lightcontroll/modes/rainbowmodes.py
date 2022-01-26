import threading

from lightcontroll.mode import register_as_mode
from lightcontroll.modeutils import genRange,adjustBrightness
from configs.dinoconf import Config

print('Loading rainbow-mode')

def wheel(pos):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        r = g = b = 0
    elif pos < 85:
        r = int(pos * 3)
        g = int(255 - pos * 3)
        b = 0
    elif pos < 170:
        pos -= 85
        r = int(255 - pos * 3)
        g = 0
        b = int(pos * 3)
    else:
        pos -= 170
        r = 0
        g = int(pos * 3)
        b = int(255 - pos * 3)
    return (r, g, b)


@register_as_mode('rainbow_cycle', 'Regenbogen :D', description='AAAAAAAAAAAAAAAAAAAa')
def rainbow_cycle(event: threading.Event,pixels, params,**kwargs):
    print('Start rainbows')
    #pixels = neopixel.NeoPixel(board.D18, Config['lightcontroll']['pixels'], brightness=1.0, auto_write=False, pixel_order=neopixel.GRB)
    while not event.wait(0.05):
        for i in range(Config['lightcontroll']['pixels']):
            pixel_index = (i * 256 // Config['lightcontroll']['pixels']) + int(genRange(0,255,iterTime=10))
            pixels[i] = adjustBrightness(wheel(pixel_index & 255), Config['lightcontroll']['brightness'])
        pixels.show()
