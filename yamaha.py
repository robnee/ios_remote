#! /usr/bin/python3

'''
python code to control Yamaha AV receiver
'''

import re
import socket


MODELNAME = "@SYS:MODELNAME"
checkhost = "8.8.8.8"
checkhost = "google.com"
checkport = 80

class yamaha:
    def __init__(self, port, hostname=None):
        self.port = port
        self.hostname = hostname
        self.request_id = 0

    def get_local_ip_address():
      ''' Returns the ip address running the python interpreter '''
      # connecting to a UDP address doesn't send packets
      s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
      s.connect((checkhost, checkport))
      print(checkhost, checkport)
      
      return s.getsockname()[0]

    def check_connect(self):
        if self.hostname is None:
            raise ValueError('no hostname')
        pass

    def request(self, hostname, timeout, name, value):
        self.request_id += 1
        msg = name + "=" + value + "\r\n"

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect((hostname, self.port))
        except:
            print("cant connect to", hostname, "on", self.port)
            return None

        try:
            s.sendall(bytes(msg, 'utf-8'))
            s.settimeout(0.05)
            response = ''
            while(True):
                data = s.recv(1024)
                if(not data):
                    break
                response = response + data.decode()
        except socket.timeout:
            pass
        except socket.error as msg:
            return None
        finally:
            s.close()
            s = None

        response = response.rstrip('\n\r')
        
        if __debug__: print('request {}: {}={}'.format(self.request_id, name, value))
        if __debug__: print('response {}: \'{}\''.format(self.request_id, response))
        
        # decode data and check if response indicates error
        if response == "@UNDEFINED" or response == '@RESTRICTED':
            return None

        #print('respons2:', data2.decode())
        results = {}
        # Build a dict of the results
        p = re.compile(r"(.*)=(.*)\s*", re.IGNORECASE)
        for x in response.split("\r\n"):
            if(x):
                m = p.match(x)
                results[m.group(1)] = m.group(2)
        
        return results

    def get(self, name):
        self.check_connect()

        return self.request(self.hostname, 0.10, name, '?')
    
    def put(self, name, value):
        self.check_connect()

        # Protocol won't answer if we try to PUT a value that is already
        # set to the same value.  Get it first so we can check
        results = self.get(name)
        if(results and name in results and results[name] == value):
            return results
        else:
            return self.request(self.hostname, 0.10, name, value)
        
    def ping(self, hostname, timeout=4):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect((hostname, self.port))
            s.sendall(bytes(MODELNAME + "=?\r\n", 'utf-8'))
            data = s.recv(1024)
            s.close()
            s = None
            
            if len(data) > 0: return True
        
        except socket.error as msg:
            s.close()
            s = None
            
        return False

    def discover(self):
        self.local_host = socket.gethostname()
        self.local_ip = yamaha.get_local_ip_address()
        host_address = self.local_ip.split('.')

        start = 1
        end = 254
    
        while(start <= end):
            host_address[3] = str(start)
            hostname = '.'.join(host_address)

            ret = self.ping(hostname, 0.5)
            if (ret):
                self.hostname = hostname
                break

            start += 1

# ----------------------------------------------------------------------------

if __name__ == '__main__':    
    port = 50000
    hostname = None
    a = yamaha(port, hostname)
    a.discover()
    print("receiver at ", a.hostname)

    print("pwr", a.put("@MAIN:PWR", "On"))
    print("get vol", a.get("@MAIN:VOL"))
    print("vol bad", a.put("@MAIN:VOL", 'Up 2 Db'))
    print("vol good", a.put("@MAIN:VOL", 'Down 2 dB'))
    print("pwr", a.put("@MAIN:PWR", "Standby"))
    
# ----------------------------------------------------------------------------
