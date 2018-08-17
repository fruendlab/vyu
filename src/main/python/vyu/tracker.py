from contextlib import contextmanager
import imageio
import numpy as np

from vyu.image import image2position
from vyu.timer import Timer


class EyeTracker(object):

    def __init__(self, camera='<video0>'):
        self.transform_matrix = np.eye(2)
        self.transform_bias = np.zeros(2)
        self.reader = imageio.get_reader(camera)

    def wait_for_fixation(self, target_area, patience=0.2):
        timer = Timer()
        for frame in self.reader:
            centroid = self.image2screen(image2position(frame))
            if centroid in target_area:
                if timer.start_or_check(patience):
                    return
            else:
                timer.clear()

    def image2screen(self, img_coords):
        screen_coords = np.dot(self.transform_matrix, img_coords)
        screen_coords += self.transform_bias
        return screen_coords

    @contextmanager
    def calibrate(self):
        raise NotImplementedError
