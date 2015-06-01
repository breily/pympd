import mpd

class Control(object):
    def __init__(self, host='192.168.1.131', port=6600, daemon=None):
        if daemon is None: self.daemon = mpd.MPD(host, port)
        else: self.daemon = daemon

    # Apparently if a method exists it will get called instead of __getattr__
    def play(self):
        print 'play'

    def __getattr__(self, attr):
        return self.daemon.__getattr__(attr)
