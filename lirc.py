import socket
import time
from threading import Lock

#from .exceptions import InvalidResponseError, LircError

class InvalidResponseError(Exception):
    pass


class LircError(Exception):
    pass
    

class LircPy():
    """
    A connection to a LIRC instance.
    TCP Listening has to be enabled in the lirc configuration.
    See the LIRC docs about the Socket Command Interface for more details.
    Any method communicating with LIRC
    - blocks until the command was processed by LIRC
    - throw a lircpy.InvalidResponseError when the response is invalid
    - throw a lircpy.LircError when LIRC reports an error
    - returns the Resposne from LIRC as string
    """
    def __init__(self, lirc_host='localhost', lirc_port=8765):
        self.lirc_host = lirc_host
        self.lirc_port = lirc_port

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.lirc_host, self.lirc_port))
        self.sf = self.s.makefile()

        self._last_sent = {}

        self.lock = Lock()

    def _send(self, command):
        """ Send a raw socket command to LIRC. """
        command = command.strip()

        with self.lock:
            self.s.send((command.strip()+'\n').encode())
            i = 0
            data_end = None
            cmd_state = None
            data = ''
            while True:
                line = self.sf.readline().strip()
                print('line:', line)
                if i == 0:
                    if line != 'BEGIN':
                        raise InvalidResponseError('Expected {0!r} but got {1!r}'.format('BEGIN', line))
                elif i == 1:
                    if line != command:
                        raise InvalidResponseError('Expected {0!r} but got {1!r}'.format(command, line))
                elif i == 2:
                    if line not in ('SUCCESS', 'ERROR'):
                        raise InvalidResponseError('Expected {0!r} or {1!r} but got {2!r}'.format('SUCCESS',
                                                                                                  'ERROR', line))
                    cmd_state = line
                elif i == 3:
                    if line == 'END':
                        break
                    if line != 'DATA':
                        raise InvalidResponseError('Expected {0!r} or {1!r} but got {2!r}'.format('END', 'DATA', line))
                elif i == 4:
                    if not line.isdigit():
                        raise InvalidResponseError('Expected data length integer but got {0!r}'.format(line))
                    data_end = 5+int(line)
                elif i < data_end:
                    data += line+'\n'
                elif i == data_end:
                    if line != 'END':
                        raise InvalidResponseError('Expected {0!r} but got {1!r}'.format('END', line))
                    break
                i += 1

        if cmd_state == 'ERROR':
            raise LircError(data if data else None)

        return data

    def _sent(self, remote_control, button_name):
        if remote_control not in self._last_sent:
            self._last_sent[remote_control] = {}
        self._last_sent[remote_control][button_name] = time.time()

    def send_once(self, remote_control, button_name, repeats=None):
        """ Send the SEND_ONCE command. """
        if repeats is None:
            result = self._send(' '.join(('SEND_ONCE', remote_control, button_name)))
        else:
            result = self._send(' '.join(('SEND_ONCE', remote_control, button_name, str(repeats))))
        self._sent(remote_control, button_name)
        return result

    def send_start(self, remote_control, button_name):
        """ Send  the SEND_START command. """
        result = self._send(' '.join(('SEND_START', remote_control, button_name)))
        self._sent(remote_control, button_name)
        return result

    def send_stop(self, remote_control, button_name):
        """ Send  the SEND_STOP command. """
        result = self._send(' '.join(('SEND_STOP', remote_control, button_name)))
        self._sent(remote_control, button_name)
        return result

    def get_button_list(self, remote_control):
        """
        Get all available buttons for a remote (using the LIST command).
        Returns a dictionary with the button names as keys and the raw data as values.
        """
        data = self._send(' '.join(('LIST', remote_control)))
        return dict([reversed(line.split(' ', 1)) for line in data.strip().split('\n')])

    def set_inputlog(self, path=None):
        """ Send  the SET_INPUTLOG command. """
        if path is None:
            return self._send('SET_INPUTLOG')
        else:
            return self._send(' '.join(('SEND_INPUTLOG', path)))

    def drv_option(self, key, value):
        """ Send the DRV_OPTION command. """
        return self._send(' '.join(('DRV_OPTION', key, str(value))))

    def simulate(self, key_data):
        """ Send the SIMULATE command. """
        return self._send('SIMULATE '+key_data)

    def set_transmitters(self, transmitter_mask):
        """ Send the SET_TRANSMITTER command. """
        return self._send('SET_TRANSMITTERS '+transmitter_mask)

    def get_version(self):
        """ Get the LIRC version (using the VERSION command). """
        return self._send('VERSION').strip()

    def get_last_sent(self, remote_control, button_name):
        """ Get the timestamp when this button on was pressed (cached locally) or None. """
        return self._last_sent.get(remote_control, {}).get(button_name)
        

def main():
    lirc = LircPy('remote')
    print(lirc.get_button_list('PANTV'))
    print(lirc.get_version())

            
if __name__ == '__main__':
    main()
