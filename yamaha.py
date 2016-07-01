#! /usr/bin/python3

'''
python code to control Yamaha AV receiver
'''

import re
import socket


MODELNAME="@SYS:MODELNAME"

class yamaha:
    def __init__(self, port):
        self.port = port

    def get_local_ip_address():
      ''' Returns the ip address running the python interpreter '''
      # connecting to a UDP address doesn't send packets
      s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
      s.connect(('8.8.8.8', 0))
      
      return s.getsockname()[0]

    def check_connect(self):
        pass

    def request(self, name, value):
        try:
            results = {}
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.25)
            s.connect((self.receiver_ip, self.port))
            
            msg = name + "=" + value + "\r\n"
            s.sendall(bytes(msg, 'utf-8'))
            data = s.recv(1024)
            s.close ()
            s = None

            # Build a dict of the results
            p = re.compile(r"(.*)=(.*)\s*", re.IGNORECASE)
            for x in data.decode().split("\r\n"):
                if (x):
                    m = p.match(x)
                    results[m.group(1)] = m.group(2) 
                    
        except socket.error as msg:
            s.close()
            s = None
            print(msg)
            
        return results

    def get(self, name):
        self.check_connect()

        return self.request(name, '?')
    
    def put(self, name, value):
        self.check_connect()

        # Protocol won't answer if we try to PUT a value that is already
        # set to the same value.  Get it first so we can check
        results = self.get(name)
        if(results[name] == value):
            return results
        else:
            return self.request(name, value)
        
    def ping(self, hostname, timeout = 4):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect((hostname, self.port))
            s.sendall(bytes(MODELNAME + "=?\r\n", 'utf-8'))
            data = s.recv(1024)
            s.close ()
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

            ret = self.ping(hostname, 1)
            if (ret):
                self.receiver_ip = hostname
                break;

            start += 1

#--------------------------------------------------------------------------------

if __name__ == '__main__':     
    port=50000
    a = yamaha(port)
    a.discover()
    print("receiver at ", a.receiver_ip)

    res = a.put("@MAIN:PWR", "On")
    print("pwr", res)

#--------------------------------------------------------------------------------
