from contextlib import contextmanager


class EyeTracker(object):

    def __init__(self):
        self.transform_matrix = np.eye(2)
        self.transform_bias = np.zeros(2)

    def wait_for_fixation(self, loc, patience=0.2):
        raise NotImplementedError

    @contextmanager
    def calibrate(self):
        raise NotImplementedError
