from unittest import TestCase
import numpy.testing as npt

import numpy as np

from vyu.calibration import estimate_matrices


class TestEstimateMatrices(TestCase):

    def test_identity(self):
        target_locations = [(1, 1), (0, 0), (5, 2), (-1, 1), (-1, -1)]
        image_locations = [(1, 1), (0, 0), (5, 2), (-1, 1), (-1, -1)]

        A, b = estimate_matrices(target_locations, image_locations)

        npt.assert_almost_equal(A, np.eye(2))
        npt.assert_almost_equal(b, np.zeros(2))

    def test_full_rank_example(self):
        image_locations = [(1, 1), (0, 0), (5, 2), (-1, 1), (-1, -1)]
        A_ = np.array([[1, .2], [.3, .9]])
        b_ = np.array([2, 5.])
        target_locations = np.dot(A_, np.transpose(image_locations)).T
        target_locations += b_.reshape((1, 2))

        A, b = estimate_matrices(target_locations, image_locations)

        npt.assert_almost_equal(A, A_)
        npt.assert_almost_equal(b, b_)
