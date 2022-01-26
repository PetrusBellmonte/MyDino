import websockets


class Connection:
    def __init__(self, websocket: websockets.WebSocketServerProtocol, manager):
        self.websocket: websockets.WebSocketServerProtocol = websocket
        self.full_intro = None

    def init(self, full_intro):
        assert self.full_intro is None
        # TODO Sanity-Checks
        self.full_intro = full_intro
        self.full_intro['args']['cached'] = True

    @property
    def origin(self):
        if self.full_intro is None:
            return None
        return self.full_intro['origin']

    @property
    def intro(self):
        try:
            return self.full_intro['args']
        except (TypeError, KeyError):
            return None

    @property
    def typ(self):
        try:
            return self.intro['type']
        except (TypeError, KeyError):
            return None


class ConnectionManager(dict):
    def __init__(self):
        super().__init__()
        self._origins = {}
        self._typs = {}
        self._modes = {}
        self._mode_bib = {}

    def __getitem__(self, item):
        if item in self._origins:
            return self._origins[item]
        return super().__getitem__(item)

    def init(self, websocket, full_intro):
        # Init Object
        self[websocket].init(full_intro)
        # Register Origins
        self._origins[self[websocket].origin] = websocket
        # Register Typ
        if self[websocket].typ not in self._typs:
            self._typs[self[websocket].typ] = []
        self._typs[self[websocket].typ].append(websocket)
        # Register _modes
        if self[websocket].typ == 'DINO':
            for mode in self[websocket].intro['possibleModes']:
                if mode['type'] not in self._modes:
                    self._modes[mode['type']] = 0
                    self._mode_bib[mode['type']] = mode
                self._modes[mode['type']] +=1

    def add(self, websocket: websockets.WebSocketServerProtocol):
        self[websocket] = Connection(websocket, self)

    def __delitem__(self, key):
        self.remove(key)

    def remove(self, websocket):
        if websocket not in self:
            return
        # Unregister origin
        if self[websocket].origin in self._origins:
            del self._origins[self[websocket].origin]
        # Unregister Typ
        if self[websocket].typ in self._typs:
            self._typs[self[websocket].typ].remove(websocket)
            if len(self._typs[self[websocket].typ])==0:
                del self._typs[self[websocket].typ]
        # Unregister Methods
        if self[websocket].typ == 'DINO':
            for mode in self[websocket].intro['possibleModes']:
                self._modes[mode['type']] -=1
                if self._modes[mode['type']] == 0:
                    del self._modes[mode['type']]
                    del self._mode_bib[mode['type']]
        #Delete object
        super().__delitem__(websocket)

    def websockets(self):
        return list(self.keys())

    def availableModes(self):
        dns = len(self._typs.get('DINO',[]))
        return [self._mode_bib[mid] for mid,c in self._modes.items() if c == dns]
