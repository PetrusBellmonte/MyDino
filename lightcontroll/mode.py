from typing import Dict, Union
import threading


class Parameter:
    def __init__(self, idName, name, description='', typ='NUMBER', unit=None, defaultValue=None, value=None):
        self.idName = idName
        self.name = name
        self.description = description
        self.typ = typ
        self.unit = unit
        self.defaultValue = defaultValue
        self.value = value if value is not None else defaultValue

    def json(self):
        return {
            "name": self.name,
            "description": self.description,
            "type": self.typ,
            "unit": self.unit,
            "defaultValue": self.defaultValue,
            "value": self._value
        }

    def update(self, jsn):
        if 'value' in jsn:
            self.value = jsn['value']

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value

    def __eq__(self, other):
        if not isinstance(other, Parameter):
            return False
        return other.idName == self.idName and other.value == self.value and other.typ == self.typ

    def __hash__(self):
        return hash((self.idName, self.typ, self.value))

class ColorParameter(Parameter):
    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if isinstance(value,str):
            value = value.strip(' \t\r#,.')
            assert len(value) ==6, f'"#{value}" has a strange length'
            self._value =(int(value[:2],16),int(value[2:-2],16),int(value[-2:],16))
        else:
            self._value = value
    def json(self):
        ret = super().json()
        ret['value'] = '#'+''.join(hex(i+2048)[-2:] for i in self._value)
        ret['defaultValue'] = '#'+''.join(hex(i+2048)[-2:] for i in self.defaultValue)
        return ret

class Mode:
    MODES = {}

    def __init__(self, idName, name, description='', params: Dict[Union[str, int], Parameter] = None):
        self.idName = idName
        self.name = name
        self.description = description
        self.params: Dict[Union[str, int], Parameter] = {} if params is None else params

    def execute(self, event: threading.Event,neoPix,**kwargs):
        # Dummy mode that does nothing
        while not event.wait(0.1):
            pass

    def json(self):
        return {"type": self.idName,
                "name": self.name,
                "description": self.description,
                "params": {i: p.json() for i, p in self.params.items()}}

    def update(self, jsn):
        for key in jsn['params']:
            if key in self.params:
                self.params[key].update(jsn['params'][key])

    @classmethod
    def fromJson(cls,jsn):
        assert jsn['type'] in cls.MODES, f'Unknown mode {jsn["type"]}'
        mode = cls.MODES[jsn['type']](jsn)
        mode.update(jsn)
        return mode
    @classmethod
    def fromId(cls,modeID):
        assert modeID in cls.MODES, f'Unknown mode {modeID} {Mode.MODES}'
        mode = cls.MODES[modeID]()
        return mode

    def __eq__(self, other):
        if not isinstance(other, Mode):
            return False
        return self.idName == other.idName and len(self.params) == len(other.params) and all(pid in other.params and param == other.params[pid] for pid, param in self.params.items())

    def __hash__(self):
        return hash((self.idName, *sorted(hash(p) for p in self.params.values())))


class FuncMode(Mode):
    def __init__(self, idName, name, description='', params: Dict[Union[str, int], Parameter] = None, exec_func=None):
        super().__init__(idName, name, description, params if params is None else params.copy())
        assert exec_func is not None
        self.exec_func = exec_func

    def execute(self, event: threading.Event,neoPix,**kwargs):
        self.exec_func(event,neoPix,self.params,**kwargs)


def register_as_mode(idName, name, description='', params: Dict[Union[str, int], Parameter] = None):
    def deco(func):
        if idName in Mode.MODES:
            raise Exception(f'Module with name {idName} already exists.')
        Mode.MODES[idName] = lambda *args: FuncMode(idName, name, description,params if params is None else params.copy(), exec_func=func)
        return func

    return deco
