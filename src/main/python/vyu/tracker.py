import os
import signal
from contextlib import contextmanager, closing
from multiprocessing import Process, SimpleQueue
import imageio
import numpy as np

from vyu.image import image2position
from vyu.timer import Timer
from vyu import calibration


class TimeOutError(Exception):
    pass


class EyeTracker(object):

    def __init__(self, camera='<video0>'):
        # Initialize transformation from image2screen to identity
        # (i.e. do nothing)
        self.transform_matrix = np.eye(2)
        self.transform_bias = np.zeros(2)
        self.queue = SimpleQueue()
        self.camera_process = Process(target=collect_frames, args=(camera, self.queue))
        self.camera_process.start()

    def wait_for_fixation(self, target_area, patience=0.2, log=False, timeout=float('inf'), callback=None):
        timer = Timer()
        all_timer = Timer()
        all_timer.start()
        print('Trying to get reader')
        # for frame in imageio.get_reader(self.reader):
        while not self.queue.empty():
            self.queue.get()

        while True:
            pos = self.queue.get()
            centroid = self.image2screen(pos)
            if log is True:
                print(pos, centroid)
            if centroid in target_area:
                if timer.start_or_check(patience):
                    return
            else:
                timer.clear()
            if all_timer.check_time(timeout):
                raise TimeOutError
            if callback is not None:
                callback(centroid)

    def image2screen(self, img_coords):
        screen_coords = np.dot(self.transform_matrix, img_coords)
        screen_coords += self.transform_bias
        return screen_coords

    @contextmanager
    def calibrate(self):
        calibrator = calibration.Calibrator(self.queue)

        yield calibrator

        A, b = calibration.estimate_matrices(calibrator.target_locations,
                                             calibrator.image_locations)
        self.transform_matrix = A
        self.transform_bias = b

    @property
    def current_eye_position(self):
        while True:
            pos = self.queue.get()
            if self.queue.empty():
                break
        return self.image2screen(pos)

    def stop(self):
        self.camera_process.terminate()
        os.kill(self.camera_process.pid, signal.SIGKILL)


def collect_frames(camera, queue):
    with closing(imageio.get_reader(camera)) as reader:
        for i, frame in enumerate(reader):
            location = image2position(frame)
            queue.put(location)
