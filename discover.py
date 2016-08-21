import socket


checkhost = "google.com"
checkport = 80

class Discoverable():
    ''' discover local host listening on giver port '''

    def get_local_ip_address():
      ''' Returns the ip address running the python interpreter '''
      # connecting to a UDP address doesn't send packets
      s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
      s.connect((checkhost, checkport))
      
      return s.getsockname()[0]

    def discover(self):
        ''' run a search '''
        self.local_host = socket.gethostname()
        self.local_ip = Discoverable.get_local_ip_address()
        print('IP:', self.local_ip)
        
        # See if we appear to be on a lan otherwise skip
        if not self.local_ip.startswith('192.168.') and not self.local_ip.startswith('10.'):
            return None

        host_address = self.local_ip.split('.')
        
        for addr in range(1, 255):
            host_address[3] = str(addr)
            hostname = '.'.join(host_address)

            if self.ping(hostname, self.port):
                return hostname
        

if __name__ == '__main__':
    pass

