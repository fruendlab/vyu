from unittest import TestCase, mock
import signal

from vyu import tracker


class TestTrackerWaitForFixation(TestCase):

    def setUp(self):
        self.camera_patch = mock.patch('vyu.tracker.CameraProcess')
        self.timer_patch = mock.patch('vyu.tracker.Timer')

        self.mock_camera = self.camera_patch.start()
        self.mock_timer = self.timer_patch.start()

        self.fixation_timer = mock.Mock()
        self.total_timer = mock.Mock()
        self.mock_timer.side_effect = [self.fixation_timer,
                                       self.total_timer]
        self.total_timer.check_time.return_value = False

        self.mock_position = (1., 1.)
        self.mock_camera_ = self.mock_camera.return_value
        self.mock_camera_.get_last_n_frames.side_effect = [
            [self.mock_position],
            [self.mock_position]]

        self.mock_area = mock.MagicMock()

    def tearDown(self):
        mock.patch.stopall()

    def test_init_creates_camera_but_doesnt_start(self):
        tracker.EyeTracker('ANY_CAMERA')
        self.mock_camera.assert_called_once_with('ANY_CAMERA')
        self.mock_camera.return_value.assert_not_called()

    def test_time_is_up(self):
        patience = 0.2

        T = tracker.EyeTracker('ANY_CAMERA')

        T.image2screen = mock.Mock()
        self.mock_area.__contains__.return_value = True
        self.fixation_timer.start_or_check.return_value = True

        T.wait_for_fixation(self.mock_area, patience=patience)

        self.mock_camera_.get_last_n_frames.assert_called_once_with(1)
        T.image2screen.assert_called_once_with(
            self.mock_position)
        self.mock_area.__contains__.assert_called_once_with(
            T.image2screen.return_value)
        self.fixation_timer.start_or_check.assert_called_once_with(patience)

    def test_time_is_after_second_frame(self):
        patience = 0.2

        T = tracker.EyeTracker('ANY_CAMERA')
        T.image2screen = mock.Mock()

        self.mock_area.__contains__.return_value = True
        self.fixation_timer.start_or_check.side_effect = [False, True]

        T.wait_for_fixation(self.mock_area, patience=patience)

        self.assertEqual(
            len(self.mock_camera_.get_last_n_frames.mock_calls), 2)
        self.assertEqual(len(T.image2screen.mock_calls), 2)
        self.assertEqual(len(self.mock_area.__contains__.mock_calls), 2)
        self.assertEqual(
            len(self.fixation_timer.start_or_check.mock_calls), 2)

    def test_point_not_in_area_w_timeout(self):
        T = tracker.EyeTracker('ANY_CAMERA')
        T.image2screen = mock.Mock()

        self.mock_area.__contains__.return_value = False

        self.total_timer.check_time.side_effect = [False, True]

        with self.assertRaises(tracker.TimeOutError):
            T.wait_for_fixation(self.mock_area, patience=0.2, timeout=1.)

        self.assertEqual(len(self.fixation_timer.clear.mock_calls), 2)
        self.total_timer.check_time.has_calls([mock.call(1.), mock.call(1.)])


class TestTrackerCalibrate(TestCase):

    def setUp(self):
        self.mock_camera = mock.patch('vyu.tracker.CameraProcess').start()
        self.mock_estimate_matrices = mock.patch(
            'vyu.tracker.calibration.estimate_matrices').start()
        self.mock_estimate_matrices.return_value = ('ANY_MATRIX', 'ANY_VECTOR')

        self.tracker = tracker.EyeTracker()

    def tearDown(self):
        mock.patch.stopall()

    def test_estimates_matrices_from_calibrator(self):
        with self.tracker.calibrate() as C:
            C.target_locations = mock.Mock()
            C.image_locations = mock.Mock()

        self.mock_estimate_matrices.assert_called_once_with(
            C.target_locations,
            C.image_locations)

    def test_assigns_transformation_matrices(self):
        with self.tracker.calibrate():
            pass

        self.tracker.transform_matrix = 'ANY_MATRIX'
        self.tracker.transform_bias = 'ANY_VECTOR'


class TestCurrentEyePosition(TestCase):

    def setUp(self):
        self.mock_camera = mock.patch('vyu.tracker.CameraProcess').start()

    def tearDown(self):
        mock.patch.stopall()

    def test_current_eye_position_gets_frame_from_camera_process(self):
        mock_camera_ = self.mock_camera.return_value
        mock_camera_.get_last_n_frames.return_value = [(1, 1)]

        T = tracker.EyeTracker()

        x, y = T.current_eye_position

        self.assertEqual(x, 1)
        self.assertEqual(y, 1)

        mock_camera_.get_last_n_frames.assert_called_once_with(1)


class TestCollectFrames(TestCase):

    @mock.patch('vyu.tracker.imageio.get_reader')
    @mock.patch('vyu.tracker.image2position')
    def test_collect_frames_puts_image_position_to_queue(self,
                                                         mock_i2pos,
                                                         mock_reader):
        mock_queue = mock.Mock()
        mock_reader_ = mock_reader.return_value
        mock_reader_.__iter__.return_value = ['frame1', 'frame2']

        tracker.collect_frames('ANY_CAMERA', mock_queue)

        self.assertEqual(mock_i2pos.call_count, 2)
        mock_i2pos.assert_has_calls([mock.call('frame1'),
                                     mock.call('frame2')])
        mock_queue.put.assert_has_calls([mock.call(mock_i2pos.return_value)]*2)
        mock_reader.assert_called_once_with('ANY_CAMERA')


class TestCameraProcess(TestCase):

    def setUp(self):
        self.mock_process = mock.patch('vyu.tracker.Process').start()
        self.mock_queue = mock.patch('vyu.tracker.SimpleQueue').start()

    def testDown(self):
        mock.patch.stopall()

    def test_init_stores_but_doesnt_start(self):
        C = tracker.CameraProcess('ANY_CAMERA')
        self.assertEqual(C.camera, 'ANY_CAMERA')
        self.assertIsNone(C.process)

    def test_start_creates_process(self):
        C = tracker.CameraProcess('ANY_CAMERA')
        C.start()
        self.mock_process.assert_called_once_with(
            target=tracker.collect_frames,
            args=('ANY_CAMERA', self.mock_queue.return_value))

    @mock.patch('vyu.tracker.os.kill')
    def test_stop_terminates_kills_and_sets_process_to_none(self,
                                                            mock_kill):
        C = tracker.CameraProcess('ANY_CAMERA')
        proc = mock.Mock()
        C.process = proc

        C.stop()

        proc.terminate.assert_called_once_with()
        mock_kill.assert_called_once_with(proc.pid, signal.SIGKILL)
        self.assertIsNone(C.process)

    def test_get_last_n_frames_returns_last_n_positions(self):
        mock_queue_ = self.mock_queue.return_value
        mock_queue_.get.side_effect = list(range(10))
        mock_queue_.empty.side_effect = [False]*8 + [True]

        C = tracker.CameraProcess('ANY_CAMERA')

        pos = C.get_last_n_frames(3)
        self.assertSequenceEqual(pos, [6, 7, 8])

    def test_get_last_n_frames_gets_first_and_then_checks(self):
        mock_queue_ = self.mock_queue.return_value
        mock_queue_.get.side_effect = list(range(10))
        mock_queue_.empty.return_value = True

        C = tracker.CameraProcess('ANY_CAMERA')

        pos = C.get_last_n_frames(1)
        self.assertSequenceEqual(pos, [0])
