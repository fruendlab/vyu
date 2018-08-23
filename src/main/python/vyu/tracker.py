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
        self.camera_process = CameraProcess(camera)

    def wait_for_fixation(self, target_area, **kwargs):
        """Wait until a fixation is detected

        Args:
            target_area (area.Area)
                should describe the area in which the fixation should occur
            patience (float)
                required duration of the fixation in seconds [Default: 0.2]
            log (bool)
                print detected positions [Default: False]
            timeout (float)
                raise error if fixation is not detected after x seconds
                [Default: inf]
        """
        patience = kwargs.setdefault('patience', 0.2)
        log = kwargs.setdefault('log', False)
        timeout = kwargs.setdefault('timeout', float('inf'))
        callback = kwargs.setdefault('callback', None)

        fixation_timer = Timer()
        total_timer = Timer()
        total_timer.start()

        while True:
            pos, = self.camera_process.get_last_n_frames(1)
            centroid = self.image2screen(pos)
            if log is True:
                print(pos, centroid)
            if centroid in target_area:
                if fixation_timer.start_or_check(patience):
                    return
            else:
                fixation_timer.clear()

            if total_timer.check_time(timeout):
                raise TimeOutError

            if callback is not None:
                callback(centroid)

    def image2screen(self, img_coords):
        screen_coords = np.dot(self.transform_matrix, img_coords)
        screen_coords += self.transform_bias
        return screen_coords

    @contextmanager
    def calibrate(self):
        calibrator = calibration.Calibrator(self.camera_process)

        yield calibrator

        A, b = calibration.estimate_matrices(calibrator.target_locations,
                                             calibrator.image_locations)
        self.transform_matrix = A
        self.transform_bias = b

    @property
    def current_eye_position(self):
        pos, = self.camera_process.get_last_n_frames(1)
        return self.image2screen(pos)

    def start(self):
        self.camera_process.start()

    def stop(self):
        self.camera_process.stop()

    def __enter__(self):
        self.start()

    def __exit__(self, *args, **kwargs):
        self.stop()


class CameraProcess(object):

    def __init__(self, camera):
        self.camera = camera
        self.queue = SimpleQueue()
        self.process = None

    def start(self):
        self.process = Process(target=collect_frames,
                               args=(self.camera, self.queue))

    def stop(self):
        self.process.terminate()
        os.kill(self.process.pid, signal.SIGKILL)
        self.process = None

    def get_last_n_frames(self, n=1):
        positions = []
        while True:
            positions.append(self.queue.get())
            if self.queue.empty() and len(positions) >= n:
                break
        return positions[-n:]


def collect_frames(camera, queue):
    with closing(imageio.get_reader(camera)) as reader:
        for i, frame in enumerate(reader):
            location = image2position(frame)
            queue.put(location)
