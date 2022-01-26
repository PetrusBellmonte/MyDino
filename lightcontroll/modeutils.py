import time, math

def genRange(start, end, iterTime):
    return start +(end-start)*(time.time()%iterTime)/iterTime

def genTriangleWave(mn=-1,mx=1,iterTime=10):
    return mn+abs((time.time()%iterTime)-(iterTime/2))/iterTime * 2 *(mx-mn)

def genSinWave(mn=-1, mx=1, iterTime=10):
    return (mx+mn)/2+math.sin(2*math.pi*(time.time()%iterTime)/iterTime)*(mx-mn)/2

def genSquareWave(low=-1, high=1, iterTime=10):
    return low if time.time()%iterTime<iterTime/2 else high

def adjustBrightness(color, brightness=1):
    import adafruit_fancyled.adafruit_fancyled as fancy
    #return int(color[0]*brightness),int(color[1]*brightness),int(color[2]*brightness)
    return fancy.denormalize(fancy.gamma_adjust(fancy.CRGB(*color),brightness=brightness))