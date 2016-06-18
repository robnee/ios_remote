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


def disc():
  hostname = socket.gethostname()
  print(hostname)

  print(get_local_ip_address())

  start = 1
  end = 254

  while(start <= end):
    print(start)

    start += 1

disc()

