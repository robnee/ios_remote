import yamaha
import queue
import threading

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
