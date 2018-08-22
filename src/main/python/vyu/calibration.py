import numpy as np


class EmptyTrackingError(Exception):
    pass


class Calibrator(object):

    def __init__(self, queue, nframes=15):
        self.nframes = nframes
        self.queue = queue
        self.target_locations = []
        self.image_locations = []

    def append(self, target_location):
        image_locations = []
        while not self.queue.empty():
            image_locations.append(self.queue.get())

        if not image_locations:
            raise EmptyTrackingError

        image_location = np.mean(image_locations[-self.nframes:], 0)
        print('Adding target_location={}, image_location={}'
              .format(target_location, image_location))
        self.target_locations.append(target_location)
        self.image_locations.append(image_location)


def estimate_matrices(target_locations, image_locations):
    targets = np.array(target_locations)
    features = np.array(image_locations)
    features = np.c_[features, np.ones(features.shape[0], 'd')]
    #gfeatures = np.r_[features, np.eye(3)]
    # targets = np.r_[targets, np.zeros((3, 2))]

    parameters = []
    for i in range(2):
        y = targets[:, i]
        w = np.linalg.lstsq(features, y)[0]
        parameters.append(w)
    parameters = np.array(parameters)
    return parameters[:, :2], parameters[:, 2]
