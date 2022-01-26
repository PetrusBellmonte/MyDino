
import os,sys
from typing import Optional, Tuple

if __name__ == '__main__':
    sys.path.append(os.path.dirname(__file__))

from configs.dinoconf import Config


class ConfigDialogeEcxeption(BaseException):
    pass


def confirm(msg='Confirm?', default=True, pos=None, neg=None, displayOptions=False, retry=None, casesensitive=False) -> Optional[bool]:
    pos = ['y', 'yes'] if pos is None else pos
    neg = ['n', 'no'] if neg is None else neg
    retry = -1 if retry == 0 else None

    assert len(pos) > 0, 'There must be a affirmative/positive option to choose from.'
    assert len(neg) > 0, 'There must be a declining/negative option to choose from.'

    if displayOptions:
        posopts = '|'.join(pos)
        negopts = '|'.join(neg)
        if default == True:
            posopts = posopts.upper()
        elif default == False:
            negopts = negopts.upper()
        msg = msg.strip() + f' ({posopts}/{negopts})'

    while retry != 0:
        res = input(msg).strip()
        if casesensitive:
            res = res.lower()

        if res == '' and default is not None:
            return default
        if res in pos:
            return True
        if res in neg:
            return False
        print('Please answer', ', '.join((pos + neg)[:-1]))
        retry -= 1
    raise ConfigDialogeEcxeption("Too many retries.")


def getValue(msg='', cast=None, default=None, options=None, displayDefault=True, displayOptions=False, retry=None, casesensitive=False, exceptions: Optional[Tuple[Exception]] = None):
    assert options is None or default is None or default in options, "Default must be an option."

    cast = cast if cast is not None else lambda x: x
    retry = -1 if retry == 0 else None

    if displayOptions:
        msg = msg.strip() + f' ({"|".join(s if s != default else f"[{s}]" for s in options)})'
    elif displayDefault and default is not None:
        msg = msg.strip() + f' [{default}]'
    msg += '\n> '

    if not casesensitive and options is not None:
        options = [s.lower() for s in options]

    while retry != 0:
        res = input(msg).strip()
        if not casesensitive:
            res = res.lower()

        if res == '' and default is not None:
            try:
                return cast(default)
            except exceptions:
                pass
        elif options is None or res in options:
            try:
                return cast(res)
            except exceptions:
                pass
        print('Does not recognise the answer.')


if __name__ == '__main__':
    # Get Websockets
    print('The Dino still needs some Information to phone Home.... Can you help them?')
    Config['websocket']['uri'] = getValue(msg='What\'s their home-number? (URI)', casesensitive=True).strip()
    Config['websocket']['key'] = getValue(msg='What\'s the super secret code? (KEY)', casesensitive=True).strip()
    Config['websocket']['name'] = getValue(msg='What\'s your Dino-name?', casesensitive=True).strip()
    print()

    Config['lightcontroll']['port'] = getValue(msg='Which port is the LED-strip connected to?', cast=lambda x: x.strip(), default='18', )