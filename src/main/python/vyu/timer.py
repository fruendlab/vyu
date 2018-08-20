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

    def check_time(self, time_difference):
        return time.time() - self.t0 >= time_difference

    def start_or_check(self, time_difference):
        if not self.isrunning():
            self.start()
        return self.check_time(time_difference)
