
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
    ('MAIN:SLEEP', ''), # Off 30 min 60 min 90 min
    ('MAIN:VOL', 'Up'), # Up Down 1 dB
    ('MAIN:MUTE', 'Ons'), # On Off Att -40 dB On/Off (toggle)
    ('MAIN:MAXVOL', ''), # -20 dB
    ('MAIN:INITVOLMODE', 'On'),
    ('MAIN:INITVOLLVL', ''), #-40 dB

    ('MAIN:INP', ''), # same as INPNAME

    ('MAIN:DECODERSEL', ''),
    ('MAIN:SCENE', ''),
    ('MAIN:SPTREBLE', ''),
    ('MAIN:SPBASS', ''),
    ('MAIN:PUREDIRMODE', ''),
    ('MAIN:ADAPTIVEDRC', ''),
    ('MAIN:HDMIRESOL', ''),
    ('MAIN:STRAIGHT', ''),
    ('MAIN:ENHANCER', ''),
    ('MAIN:SOUNDPRG', ''), # Surround Decoder
    ('MAIN:ADAPTIVEDSP', ''),
    ('MAIN:3DCINEMA', ''),
    ('MAIN:EXSURDECODER', ''),
    ('MAIN:2CHDECODER', '')
]

class MyController():
    def __init__(self):
        self.receiver = yamaha.yamaha(port=50000)
        self.receiver.discover()
        print(self.receiver.get('@SYS:INPNAME'))
        print(self.receiver.get('@MAIN:INP'))
        print(self.receiver.get('@SYS:INPNAME'))

        self.q = queue.Queue()
        self.t = threading.Thread(target=lambda: self.worker())
        self.t.start()
        
    def put(self, name, value):
        self.q.put((name, value))
        #print('add:', name, '=', value)
        
    def worker(self):
        print('working')
        while True:
            item = self.q.get()
            if item is None:
                break
            name, value = item
            self._put (name, value)
            self.q.task_done()
        
    def _put(self, name, value):
        return self.receiver.put(name, value)
        
    def _get(self, name):
        return self.receiver.get(name)
