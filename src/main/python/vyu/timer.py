import time


class Timer(object):

    def __init__(self):
        self.t0 = None

    def start(self):
        self.t0 = time.time()

    def clear(self):
        self.t0 = None

    def isrunning(self):
        return self.t0 is not None

    def check_time(self, dt):
        return time.time() - self.t0 >= dt

    def start_or_check(self, dt):
        if not self.isrunning():
            self.start()
        return self.check_time(dt)
