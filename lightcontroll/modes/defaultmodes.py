import threading

from lightcontroll.mode import register_as_mode, ColorParameter,Parameter
from lightcontroll.modeutils import genTriangleWave,adjustBrightness
from configs.dinoconf import Config
num_pixels = 100
print('Loading default modes')

@register_as_mode('uniColor', 'Unicolor', 'All LED have the same color.',
                  {'color': ColorParameter('color', 'color', typ='COLOR', defaultValue=(255, 255, 255))})
def uni_color(event: threading.Event,pixels, params,**kwargs):
    print('start unicolor')
    #pixels = neopixel.NeoPixel(board.D18, Config['lightcontroll']['pixels'], brightness=1.0, auto_write=False, pixel_order=neopixel.GRB)
    b = None
    while not event.wait(0.1):
        if b != Config['lightcontroll']['brightness']:
            b = Config['lightcontroll']['brightness']
            pixels.fill(adjustBrightness(color=params['color'].value,brightness=b))
            pixels.show()

@register_as_mode('pulse', 'Pulse', 'LED gets brighter an darker',
                  {'circletime': Parameter('circletime', 'Circletime', defaultValue=10,unit='s'),'color': ColorParameter('color', 'color', typ='COLOR', defaultValue=(255, 255, 255))})
def pulse_color(event: threading.Event,pixels, params,**kwargs):
    print('start pulse_color')
    #pixels = neopixel.NeoPixel(board.D18, Config['lightcontroll']['pixels'], brightness=1.0, auto_write=False, pixel_order=neopixel.GRB)
    while not event.wait(0.02):
        b = Config['lightcontroll']['brightness']
        b *= genTriangleWave(-1,1,params['circletime'].value)#abs((time.time()%params['circletime'].value)-(params['circletime'].value/2))/params['circletime'].value*2
        pixels.fill(adjustBrightness(color=params['color'].value, brightness=b))
        pixels.show()
