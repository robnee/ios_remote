
import yamaha
import queue
import threading

#------------------------------------------------------------------------------

codes = [
    ('SYS:MODELNAME', '?'),
    ('SYS:VERSION', '?'),
    ('SYS:INPNAME', '?'),
    ('SYS:INPNAMExxx', '?'), # xxx=HDMI1-5 AV1-6 VAUX AUDIO1-6 DOCK USB
    ('SYS:PWR', 'On'),
    ('SYS:REMOTECODE', 'hexcode'),

    ('MAIN:AVAIL', '?'),
    ('MAIN:ZONENAME', '?'),
    ('MAIN:SCENENAME', '?'),


    ('MAIN:PWR', 'On'),
    ('MAIN:SLEEP', ''),  # Off 30 min 60 min 90 min
    ('MAIN:VOL', 'Up'),  # Up Down 1 dB
    ('MAIN:MUTE', 'Ons'),  # On Off Att -40 dB On/Off (toggle)
    ('MAIN:MAXVOL', ''),  # -20 dB_
    ('MAIN:INITVOLMODE', 'On'),
    ('MAIN:INITVOLLVL', ''),  # -40 dB

    ('MAIN:INP', ''),  # same as INPNAME

    ('MAIN:DECODERSEL', ''),
    ('MAIN:SCENE', ''),
    ('MAIN:SPTREBLE', ''),
    ('MAIN:SPBASS', ''),
    ('MAIN:PUREDIRMODE', ''),
    ('MAIN:ADAPTIVEDRC', ''),
    ('MAIN:HDMIRESOL', ''),
    ('MAIN:STRAIGHT', ''),
    ('MAIN:ENHANCER', ''),
    ('MAIN:SOUNDPRG', ''),  # Surround Decoder
    ('MAIN:ADAPTIVEDSP', ''),
    ('MAIN:3DCINEMA', ''),
    ('MAIN:EXSURDECODER', ''),
    ('MAIN:2CHDECODER', '')
]


class MyController():
    def __init__(self, hostname=None):
        self.receiver = yamaha.yamaha(port=50000)
        if hostname is None:
            self.hostname = hostname
        elif hostname == 'auto':
            self.receiver.discover()
            self.hostname = self.receiver.hostname
            print('Discovered host controller on', self.hostname)
        else:
            self.hostname = self.receiver.hostname = hostname

        # print(self.receiver.get('@SYS:INPNAME'))

        self.q = queue.Queue()
        self.t = threading.Thread(target=lambda: self.worker())
        self.t.start()
        
        self.status = 'init'
        self.listener = None
    
    def connect(self):
        self.set_status('connected')
        
    def set_status(self, status):
        self.status = status
        if self.listener:
            self.listener(status)
        
    def add_listener(self, listener):
        self.listener = listener
        
    def put(self, name, value):
        self.q.put((name, value))
        # print('add:', name, '=', value)
        
    def worker(self):
        while True:
            item = self.q.get()
            if item is None:
                break

            name, value = item
            self._put(name, value)
            self.q.task_done()
        
    def _put(self, name, value):
        if self.hostname is not None:
            return self.receiver.put(name, value)
        else:
            print('put to null:', name, '=', value)
            return name + '=' + value
        
    def _get(self, name):
        if self.hostname is not None:
            return self.receiver.get(name)
        else:
           print('put to null:', name, '=', value)
           return name + '=' + value  
