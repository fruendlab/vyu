from unittest import TestCase, mock
import numpy.testing as npt

import numpy as np

from vyu.calibration import estimate_matrices, Calibrator, EmptyTrackingError


class TestEstimateMatrices(TestCase):

    def test_identity(self):
        target_locations = [(1, 1), (0, 0), (5, 2), (-1, 1), (-1, -1)]
        image_locations = [(1, 1), (0, 0), (5, 2), (-1, 1), (-1, -1)]

        A, b = estimate_matrices(target_locations, image_locations)

        # For this special case, we know that Ax+b should be the identity, thus
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


class TestCalibrator(TestCase):

    def setUp(self):
        self.mock_queue = mock.Mock()
        self.calibrator = Calibrator(self.mock_queue,
                                     nframes=2)

    @mock.patch('vyu.calibration.np.mean')
    def test_nframes_elements_in_queue_takes_mean_of_nframes(self, mock_mean):
        self.mock_queue.empty.side_effect = [False, False, True]
        self.mock_queue.get.return_value = (1., 1.)

        self.calibrator.append(3)

        mock_mean.assert_called_once_with([(1., 1.), (1., 1.)], 0)

    @mock.patch('vyu.calibration.np.mean')
    def test_less_elements_in_queue_takes_mean_of_less(self, mock_mean):
        self.mock_queue.empty.side_effect = [False, True]
        self.mock_queue.get.return_value = (1., 1.)

        self.calibrator.append(3)

        mock_mean.assert_called_once_with([(1., 1.)], 0)

    def test_no_elements_in_queue_raises_exception(self):
        self.mock_queue.empty.return_value = True

        with self.assertRaises(EmptyTrackingError):
            self.calibrator.append(3)

    @mock.patch('vyu.calibration.np.mean')
    def test_too_many_elements_in_queue_takes_last_nframes(self, mock_mean):
        self.mock_queue.empty.side_effect = [False, False, False, True]
        self.mock_queue.get.side_effect = [1, 2, 3]

        self.calibrator.append(3)

        mock_mean.assert_called_once_with([2, 3], 0)

    def test_results_show_up_in_locations_lists(self):
        self.mock_queue.empty.side_effect = [False, False, True]
        self.mock_queue.get.side_effect = [(1., 1.), (2., 1.)]

        self.calibrator.append((3., 3.))

        self.assertSequenceEqual(self.calibrator.target_locations,
                                 [(3., 3.)])
        npt.assert_almost_equal(self.calibrator.image_locations,
                                np.array([[1.5, 1.]]))
