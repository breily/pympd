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
        # Dict Commands return data where each key has only one value
        self.dict_commands = ['disableoutput', 'enableoutput', 'update', 'status',
            'stats']
        # List Commands return data where one key has multiple values
        self.list_commands = ['commands', 'notcommands', 'tagtypes', 'urlhandlers',
            'list']
        # Object Commands return data where multiple keys have multiple values
        # Return list of dictionaries
        self.object_commands = ['outputs', 'find']
        # None Commands don't return anything (None)
        self.none_commands = ['kill',]

    def __getattr__(self, attr):
        return lambda *args: self.execute(attr, args)

    def execute(self, cmd, args=None):
        """ Sends a command and arguments to MPD.  """
        cmd_copy = cmd
        if args is not None:
            for arg in args: cmd += ' ' + str(arg)
        self.send(cmd)
        # Basically the try/except block checks if
        # something was sent back
        if cmd_copy in self.dict_commands:
            try: return self.parse_dict( self.receive() )
            except: return {}
        if cmd_copy in self.list_commands:
            try: return self.parse_list( self.receive() )
            except: return []
        if cmd_copy in self.object_commands:
            try: return self.parse_objects( self.receive() )
            except: return [{}]
        if cmd_copy in self.none_commands:
            return None
        return {'error': 'Command not found'}

    def send(self, line):
        """
        Sends line to MPD.
        Appends new line if not present.
        Escapes if necessary.
        """
        if '\n' not in line: line += '\n'
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

    def parse_dict(self, data):
        """ Parses data received from MPD into a dictionary.  """
        ret = {}
        for line in data:
            if line[:2] == 'OK': continue
            if line[:3] == 'ACK': return {'error': line}
            tmp = line.split(':', 1)
            ret[ tmp[0] ] = tmp[1].strip()
        return ret

    def parse_list(self, data):
        """ Removes 'OK' messages from data.  """
        return [line for line in data if line[:2] != 'OK']

    def parse_objects(self, data):
        """ Returns list of dictionaries. """
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
