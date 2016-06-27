#! /usr/bin/python

import xmlrpclib
from SimpleXMLRPCServer import SimpleXMLRPCServer

def today():
#	today = datetime.datetime.today()
#	return xmlrpc.client.DateTime(today)
	return "today"

def test():
	return "hello"

host = "0.0.0.0"
port = 8000
server = SimpleXMLRPCServer((host, port))
print("Listening on port " + str(port) + "...")

server.register_function(today, "today")
server.register_function(test, "test")
server.serve_forever()

