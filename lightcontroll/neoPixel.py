import neopixel
from neopixel import NeoPixel, GRB, GRBW, RGBW


class DisconnectedNeoPixel(neopixel.NeoPixel):
    def __init__(
            self,
            n: int,
            *,
            bpp: int = 3,
            brightness: float = 1.0,
            auto_write: bool = True,
            pixel_order: str = None
    ):
        if not pixel_order:
            pixel_order = GRB if bpp == 3 else GRBW
        elif isinstance(pixel_order, tuple):
            order_list = [RGBW[order] for order in pixel_order]
            pixel_order = "".join(order_list)

        super(NeoPixel, self).__init__(n, brightness=brightness, byteorder=pixel_order, auto_write=auto_write)

    def deinit(self) -> None:
        """Blank out the NeoPixels and release the pin."""
        self.fill(0)
        self.show()

    def _transmit(self, buffer: bytearray) -> None:
        pass
