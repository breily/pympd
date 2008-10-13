"""
PyMPD - A Python interface to MPD

Usage:
    import mpd
    m = mpd.MPD('localhost', 6600)
    m.status()
    m.play()
    m.list('artist')
    etc...

Author: Brian Reily
Version: 0.0.1
"""

from socket import *

def escape(text):
    return text.replace('\\', '\\\\').replace('"', '\\"')

class AckException(Exception): pass
class ConnException(Exception): pass

class MPD(object):
    def __init__(self, host='192.168.1.131', port=6600):
        """
        Takes host and port arguments.
        Defaults to 192.168.1.131 and 6600.
        """
        self.host = host
        self.port = port
        try:
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.connect( (host, port) )
            self.file = self.sock.makefile('rb+')
        except: raise ConnException('Could not connect to %s:%s' %(host, port))

    def __getattr__(self, attr):
        return lambda *args: self.execute(attr, args)

    def execute(self, cmd, args=None):
        """ Sends a command and arguments to MPD, returns response.  """
        if args is not None:
            for arg in args: cmd += ' ' + str(arg)
        self.send(cmd)
        # Basically the try/except block checks if
        # something was sent back
        try: return self.receive()
        except: return []

    def send(self, line):
        """
        Sends line to MPD.
        Appends new line if not present.
        Escapes if necessary.
        """
        if '\n' != line[-1:]: line += '\n'
        if '\\' in line or '"' in line: line = escape(line)
        self.file.write(line)
        self.file.flush()
    
    def receive(self):
        """ Returns list of strings from MPD.  """
        data = []
        while 1:
            tmp = self.file.readline().rstrip('\n')
            data.append(tmp)    
            if tmp == 'OK': return data
            if tmp[:3] == 'ACK':
                raise AckException(tmp)
                return data

    def reset(self):
        """
        Creates a new connection to the MPD server.
        Mainly used during testing in case the connection times out.
        """
        del self.sock
        del self.file
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.connect( (self.host, self.port) )
        self.file = self.sock.makefile('rb+')
