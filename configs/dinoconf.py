from typing import Optional,Union,Any
from utils.config import newConfig, fromFile
import os

print('Load Config')
_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'dino.yml')

if os.path.exists(_file):
    Config = fromFile(_file)
else:
    Config = newConfig(file=_file)

_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'modes.yml')
if os.path.exists(_file):
    Config['lightcontroll']['modes'] = fromFile(_file)
else:
    Config['lightcontroll']['modes'] = newConfig(file=_file, typ=list)
