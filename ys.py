#! /usr/bin/python3

# Echo server program

import socket
import re
import sys

HOST = 'localhost'
PORT = 50000


class YamahaServer():
	def __init__(self, hostname, port):
		self.hostname = hostname
		self.port = port

	def run(self):
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.bind((self.hostname, self.port))
		s.listen(1)
		while 1:
			conn, addr = s.accept()
			print('Connected by', addr)
			while 1:
				data = conn.recv(1024)
				if not data:
					break

				command = data.decode()
				print("command:", command)
				p = re.compile(r"(.*)=(.*)\s*", re.IGNORECASE)
				for x in command.split("\r\n"):
					if(x):
						print("matching:", repr(x))
						# Check for a PUT or a GET
						m = p.match(x)
						if(m):
							name = m.group(1)
							value = m.group(2)
							msg = "{}=1\r\n".format(name)
							if(value == '?'):
								value = '1'

							response = "{}={}\r\n".format(name, value)
							conn.sendall(bytes(response, 'utf-8'))
			conn.close()

if __name__ == '__main__':
	print("Yamaha simulator server...")
	y = YamahaServer(HOST, PORT)
	y.run()
