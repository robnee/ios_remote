#! /usr/bin/python

'''
python code to control Yamaha AV receiver
'''


import socket

def get_local_ip_address():
  ''' Returns the ip address running the python interpreter '''
  # connecting to a UDP address doesn't send packets
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  s.connect(('8.8.8.8', 0))
  ip_address_string = s.getsockname()[0]

  return ip_address_string.split('.')


def disc(port):
    localhost = socket.gethostname()
    print(localhost)

    host_address = local_ip = get_local_ip_address()

    start = 1
    end = 54

    while(start <= end):
        host_address[3] = str(start)
        hostname = '.'.join(host_address)

        print(hostname)
        try:
            print "socket"
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            print "connect"
            s.connect((hostname, port))
            print "send"
            s.sendall(b'@SYS:MODELNAME=?\r\n')
            data = s.recv(1024)
            s.close ()
            s = None
            print(hostname, ' Received', repr(data))
        except socket.error:
            print "except"
            s.close()
            s = None

        print "inc"
        start += 1
    
port=50000
disc(port)

