import os, signal
from contextlib import contextmanager
from multiprocessing import Process, Queue
import imageio
import numpy as np

from vyu.image import image2position
from vyu.timer import Timer
from vyu import calibration


class EyeTracker(object):

    def __init__(self, camera='<video0>'):
        # Initialize transformation from image2screen to identity
        # (i.e. do nothing)
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
        queue = Queue()
        collector = Process(target=collect_frames, args=(self.reader, queue))
        calibrator = calibration.Calibrator(queue)
        collector.start()

        yield calibrator

        collector.terminate()
        # collect_frames runs infinite loop and needs to be killed
        os.kill(collector.pid, signal.SIGKILL)

        A, b = calibration.estimate_matrices(calibrator.target_locations,
                                             calibrator.image_locations)
        self.transform_matrix = A
        self.transform_bias = b


def collect_frames(reader, queue):
    for frame in reader:
        location = image2position(frame)
        queue.put(location)
