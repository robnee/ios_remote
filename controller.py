
import yamaha
import discover
import lirc

import socket
import queue
import threading
import time

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

'''\
FIOS
irsend: 0000000000000001 KEY_ASTERISK
irsend: 0000000000000002 KEY_CC
irsend: 0000000000000003 KEY_CHANNEL_DOWN
irsend: 0000000000000004 KEY_CHANNEL_PAGE_DOWN
irsend: 0000000000000005 KEY_CHANNEL_PAGE_UP
irsend: 0000000000000006 KEY_CHANNEL_UP
irsend: 0000000000000007 KEY_CURSOR_DOWN
irsend: 0000000000000008 KEY_CURSOR_ENTER
irsend: 0000000000000009 KEY_CURSOR_LEFT
irsend: 000000000000000a KEY_CURSOR_RIGHT
irsend: 000000000000000b KEY_CURSOR_UP
irsend: 000000000000000c KEY_DIGIT_0
irsend: 000000000000000d KEY_DIGIT_1
irsend: 000000000000000e KEY_DIGIT_2
irsend: 000000000000000f KEY_DIGIT_3
irsend: 0000000000000010 KEY_DIGIT_4
irsend: 0000000000000011 KEY_DIGIT_5
irsend: 0000000000000012 KEY_DIGIT_6
irsend: 0000000000000013 KEY_DIGIT_7
irsend: 0000000000000014 KEY_DIGIT_8
irsend: 0000000000000015 KEY_DIGIT_9
irsend: 0000000000000016 KEY_EXIT
irsend: 0000000000000017 KEY_FAVORITES
irsend: 0000000000000018 KEY_FIOS_TV
irsend: 0000000000000019 KEY_FORMAT_POUND
irsend: 000000000000001a KEY_FORMAT_SCROLL
irsend: 000000000000001b KEY_FORWARD
irsend: 000000000000001c KEY_FUNCTION_A
irsend: 000000000000001d KEY_FUNCTION_B
irsend: 000000000000001e KEY_FUNCTION_C
irsend: 000000000000001f KEY_FUNCTION_D
irsend: 0000000000000020 KEY_GUIDE
irsend: 0000000000000021 KEY_INFO
irsend: 0000000000000022 KEY_MENU_DVR
irsend: 0000000000000023 KEY_MENU_MAIN
irsend: 0000000000000024 KEY_OPTIONS
irsend: 0000000000000025 KEY_PAGE_DOWN
irsend: 0000000000000026 KEY_PAGE_UP
irsend: 0000000000000027 KEY_PAUSE
irsend: 0000000000000028 KEY_PLAY
irsend: 0000000000000029 KEY_POWER_OFF
irsend: 000000000000002a KEY_POWER_ON
irsend: 000000000000002b KEY_POWER_TOGGLE
irsend: 000000000000002c KEY_PREVIOUS_CHANNEL
irsend: 000000000000002d KEY_RECORD
irsend: 000000000000002e KEY_REPLAY
irsend: 000000000000002f KEY_REVERSE
irsend: 0000000000000030 KEY_SKIP
irsend: 0000000000000031 KEY_STOP
irsend: 0000000000000032 KEY_VIDEO_ON_DEMAND
irsend: 0000000000000033 KEY_WIDGETS

PANTV
irsend: 0000000000000001 KEY_HDMI1
irsend: 0000000000000002 KEY_POWEROFF
irsend: 0000000000000003 KEY_POWERON
'''

class MyAction:
    def fire(self):
        self.__fire__()


class MyFunctionAction(MyAction):
    def __init__(self, delegate=None):
        self.delegate = delegate
        
    def __fire__(self):
        if self.delegate is not None:
            self.delegate()


class MyCommandAction(MyFunctionAction):
    def __init__(self, cont, cmd, arg):
        super().__init__(lambda: cont.put(cmd, arg))


class MyTuneAction(MyAction):
    def __init__(self, cont, arg):
        if arg.isdecimal():
            self.cont = cont
            self.channel = arg
            
    def __fire__(self):
        print('fire tune', self.channel)
        for digit in self.channel:
            self.cont.put('FIOS:KEY_DIGIT_' + digit, '')
            

class YamahaComp(discover.Discoverable):
    '''Yamaha component command endpoint'''
    def __init__(self, mode):
        '''mode = None | 'auto'''
        self.status = 'init'
        self.port = 50000
        
        self.connect(mode)
        
    def connect(self, hostname=None):
        if hostname == 'auto':
            self.hostname = self.discover()
            if self.hostname is not None:
                print('Discovered host component on', self.hostname)
            else:
                print('Discovery failed')
        else:
            self.hostname = hostname
            
        # connect
        if self.hostname is not None:
            self.host = yamaha.yamaha(hostname=self.hostname, port=50000)
            self.status = 'connected'
        else:
            self.host = None
            self.status = 'disconnected'
            
    def ping(self, hostname, port, timeout=0.2):
        print(hostname, port)
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect((hostname, port))
            s.sendall(bytes(yamaha.MODELNAME + "=?\r\n", 'utf-8'))
            data = s.recv(1024)

            if len(data) > 0:
                return True
        except socket.error as msg:
            pass
        finally:
            s.close()
            s = None
      
    def put(self, name, value):
        if self.host is not None:
            return self.host.put(name, value)
        else:
            print('put to null:', name, '=', value)
            return name + '=' + value
        
    def get(self, name):
        if self.host is not None:
            return self.host.get(name)
        else:
           print('get from null:', name)
           return name + '= ?'


class LircComp(discover.Discoverable):
    '''Lirc component multi endpoint'''
    def __init__(self, mode):
        self.status = 'init'
        self.port = 8765
        
        self.connect(mode)
   
    def connect(self, hostname=None):
        if hostname == 'auto':
            self.hostname = self.discover()
            if self.hostname is not None:
                print('Discovered host component on', self.hostname)
            else:
                print('Discovery failed')
        else:
            self.hostname = hostname
            
        # connect
        if self.hostname is not None:
            self.host = lirc.LircPy(self.hostname)
            self.status = 'connected'
        else:
            self.host = None
            self.status = 'disconnected'
        
    def ping(self, hostname, port, timeout=0.2):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect((hostname, port))
            s.sendall(bytes("VERSION\n", 'utf-8'))
            data = s.recv(1024)
            print('ping:', data)
            
            if len(data) > 0:
                return True
        
        except socket.error as msg:
            pass
        finally:
            s.close()
            s = None
        
    def get(self, name):
        return None
   
    def put(self, name, value):
        if self.host is not None:
            print('put to lirc:', name, '=', value)
            remote, button = name.split(':')
            return self.host.send_once(remote, button)
        else:
            print('put to null:', name, '=', value)
            return name + '=' + value

        
class MyController():
    def __init__(self, hostname=None):
        self.q = queue.Queue()
        self.t = threading.Thread(target=lambda: self.worker())
        self.t.start()

        self.listener = None

        self.yam = YamahaComp(hostname)
        self.lirc = LircComp(hostname)
        
        self.comps = dict()
        self.comps['@MAIN'] = self.yam
        self.comps['@SYS'] = self.yam
        self.comps['FIOS'] = self.lirc
        self.comps['PANTV'] = self.lirc     

    def connect(self, hostname):
        self.yam.connect(hostname)
        self.lirc.connect(hostname)
        
    def get_status(self):
        if self.yam.status == self.lirc.status:
            return self.yam.status
        else:
            return 'disconnected'
        
    def add_listener(self, listener):
        self.listener = listener
        
    def put(self, name, value):
        self.q.put((name, value))
        print('add:', name, '=', value)
        
    def get(self, name):
        target, cmd = name.split(':')
        comp = self.comps[target]
        return comp.get(name)
                
    def worker(self):
        while True:
            item = self.q.get()
            if item is None:
                break

            name, value = item
            self._put(name, value)
            self.q.task_done()
        
    def _put(self, name, value):
        target, cmd = name.split(':')
        comp = self.comps[target]
        comp.put(name, value)
        time.sleep(0.05)

        
if __name__ == '__main__':
    mc = MyController('auto')
    
    mc.lirc.put('FIOS:KEY_MENU_MAIN', '')
    mc.lirc.put('FIOS:KEY_DIGIT_0', '')
    mc.lirc.put('FIOS:KEY_DIGIT_6', '')
    mc.lirc.put('FIOS:KEY_DIGIT_0', '')
    mc.lirc.put('FIOS:KEY_DIGIT_3', '')
    
    ch = MyTuneAction(mc, '0603')
    ch.fire()
    
