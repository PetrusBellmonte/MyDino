from __future__ import annotations
import yaml, json
from enum import Enum
from typing import TypeVar, Union, Set, Dict, Tuple, Any, Protocol, Hashable


class StoreType(Enum):
    YAML = 'YML'
    JSON = 'JSON'


T = TypeVar('T')
PathType = Tuple[Hashable]


class ChangeListener(Protocol):
    def __call__(self, path: PathType, value: Any, deleted: bool = ..., tags=..., **kwargs) -> None: ...


class ConfigException(Exception):
    pass


class NotConfigAble(ConfigException):
    pass


class YamlStateSerializer:
    def yamlDump(self, dumper: yaml.Dumper):
        raise NotImplemented()


yaml.add_multi_representer(YamlStateSerializer, lambda dumper, data: data.yamlDump(dumper), Dumper=yaml.SafeDumper)


class ChangeListenAble:
    def __init__(self, *args, **kwargs) -> None:
        self.onChangeListeners: Set[ChangeListener] = set()
        self.ownListeners: Dict[int, ChangeListener] = {}
        super().__init__(*args, **kwargs)

    def triggerOnChange(self, path: PathType, value, **kwargs) -> None:
        for listener in self.onChangeListeners:
            listener(path, value, **kwargs)

    def addOnChangeListener(self, listener: ChangeListener) -> None:
        self.onChangeListeners.add(listener)

    def removeOnChangeListener(self, listener: ChangeListener) -> None:
        if listener in self.onChangeListeners:
            self.onChangeListeners.remove(listener)


class SaveAble(ChangeListenAble):
    def __init__(self, *args, file=None, filetype: StoreType = StoreType.YAML, **kwargs):
        self.file = file
        self.filetype: StoreType = filetype
        super().__init__(*args, **kwargs)

    def triggerOnChange(self, path: PathType, value, **kwargs) -> None:
        if self.file is not None and not kwargs.get('alreadySaved', False):
            self.save()
            kwargs['alreadySaved'] = True
            super().triggerOnChange(path, value, **kwargs)
        else:
            super().triggerOnChange(path, value, **kwargs)

    def save(self):
        print('Saving', self)
        with open(self.file, 'w') as f:
            if self.filetype == StoreType.YAML:
                f.write(yaml.safe_dump(self))
            elif self.filetype == StoreType.JSON:
                f.write(json.dumps(self))
            else:
                raise ConfigException(f'Unknown/Unimplemented StoreType: {self.filetype}')

    def unlinkFile(self):
        self.file = None

    def linkToFile(self, file, filetype: StoreType = StoreType.YAML):
        self.file = file
        self.filetype = filetype


class ChangeListenerChainer(ChangeListenAble):

    def iterPathChildren(self):
        raise NotImplemented()

    def isChildren(self, obj):
        raise NotImplemented()

    def _onChange(self, obj, path: PathType, value: Any, **kwargs):
        for p, o in self.iterPathChildren():
            if o == obj:
                self.triggerOnChange((p, *path), value, **kwargs)

    def getRegisterdConfigObject(self, obj):
        obj = _getConfigObject(obj)
        if isinstance(obj, ChangeListenAble):
            if id(obj) not in self.ownListeners:
                def factory(o):
                    return lambda path, val, **kwargs: self._onChange(o, path, val, **kwargs)

                self.ownListeners[id(obj)] = factory(obj)
                obj.addOnChangeListener(self.ownListeners[id(obj)])
        return obj

    def unregisterObject(self, obj):
        if isinstance(obj, ChangeListenAble) and not self.isChildren(obj):
            obj.removeOnChangeListener(self.ownListeners[id(obj)])


class MappingChainListener(ChangeListenerChainer):
    def __setitem__(self, key, value):
        # Save old value to be removed
        try:
            old_value = self[key]
        except KeyError:
            old_value = None
        # Set and register new value
        super().__setitem__(key, self.getRegisterdConfigObject(value))
        # Remove old triggers
        self.unregisterObject(old_value)
        # Trigger change
        self.triggerOnChange((key,), self[key])

    def __delitem__(self, key):
        old_value = self[key]
        super().__delitem__(key)
        self.unregisterObject(old_value)
        self.triggerOnChange((key,), old_value, deleted=True)


class ConfigItem(MappingChainListener, SaveAble, YamlStateSerializer):
    def __getitem__(self, item)->Union[ConfigItem,int,float,str,YamlStateSerializer]:
        return super().__getitem__(item)


class ConfigList(ConfigItem, list):
    def __init__(self, ls=None, *args, **kwargs):
        super().__init__([] if ls is None else (self.getRegisterdConfigObject(e) for e in ls), *args, **kwargs)

    def iterPathChildren(self):
        yield from enumerate(self)

    def isChildren(self, obj):
        return obj in self

    def append(self, __object):
        super(ConfigList, self).append(self.getRegisterdConfigObject(__object))
        self.triggerOnChange((len(self) - 1,), __object)

    def extend(self, __iterable):
        for e in __iterable:
            self.append(e)

    def yamlDump(self, dumper: yaml.Dumper):
        return dumper.represent_list([v if not isinstance(v, SaveAble) or v.file is None else f'CONF AT {v.file}' for v in self])


class ConfigDict(ConfigItem, dict):
    def __init__(self, data=None, *args, **kwargs):
        super().__init__({} if data is None else ((k, self.getRegisterdConfigObject(e)) for k, e in data.items()), *args, **kwargs)

    def iterPathChildren(self):
        yield from self.items()

    def isChildren(self, obj):
        return obj in self.values()

    def yamlDump(self, dumper: yaml.Dumper):
        return dumper.represent_dict(dict((k, v) if not isinstance(v, SaveAble) or v.file is None else (k, f'CONF AT {v.file}') for k, v in self.items()))


def _toConfigObject(obj) -> ChangeListenAble:
    if isinstance(obj, list):
        return ConfigList(obj)
    if isinstance(obj, dict):
        return ConfigDict(obj)
    raise NotConfigAble(f'No Config-object for {type(obj).__name__}.')


def _getConfigObject(obj: T) -> Union[T, ChangeListenAble]:
    if isinstance(obj, ChangeListenAble):
        return obj
    try:
        return _toConfigObject(obj)
    except NotConfigAble:
        return obj


def newConfig(data=None, file=None, typ=dict, filetype=StoreType.YAML):
    # Adjust type if data is given
    if data is not None and isinstance(data, list):
        typ = list
    # Init Config
    if typ == dict:
        conf = ConfigDict(data, file=file, filetype=filetype)
    elif typ == list:
        conf = ConfigList(data, file=file, filetype=filetype)
    else:
        raise Exception(f'No Config of type {typ} possible.')
    # Save it
    conf.save()
    return conf


def fromFile(file, filetype=StoreType.YAML, linkFile=True):
    # Load file
    with open(file) as f:
        data = yaml.safe_load(f.read())
    # Create ConfigItem
    if isinstance(data, list):
        conf = ConfigList(data, file=file, filetype=filetype)
    else:
        conf = ConfigDict(data, file=file, filetype=filetype)
    # Unlink file if necessary
    if not linkFile:
        conf.unlinkFile()
    return conf
