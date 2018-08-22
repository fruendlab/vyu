from unittest import TestCase, mock
import signal

from vyu import tracker


class TestTrackerWaitForFixation(TestCase):

    def setUp(self):
        self.reader_patch = mock.patch('vyu.tracker.imageio.get_reader')
        self.timer_patch = mock.patch('vyu.tracker.Timer')
        self.i2pos_patch = mock.patch('vyu.tracker.image2position')
        self.frames = [mock.Mock(), mock.Mock()]

        self.mock_get_reader = self.reader_patch.start()
        self.mock_timer = self.timer_patch.start()
        self.mock_i2pos = self.i2pos_patch.start()

        self.mock_get_reader.return_value.__iter__.return_value = self.frames
        self.mock_timer_instance = self.mock_timer.return_value

        self.mock_area = mock.MagicMock()

    def tearDown(self):
        mock.patch.stopall()

    def test_init_creates_reader(self):
        tracker.EyeTracker('ANY_CAMERA')
        self.mock_get_reader.assert_called_once_with('ANY_CAMERA')

    def test_time_is_up(self):
        patience = 0.2

        T = tracker.EyeTracker('ANY_CAMERA')
        T.image2screen = mock.Mock()

        self.mock_area.__contains__.return_value = True
        self.mock_timer_instance.start_or_check.return_value = True

        T.wait_for_fixation(self.mock_area, patience)

        self.mock_i2pos.assert_called_once_with(self.frames[0])
        T.image2screen.assert_called_once_with(self.mock_i2pos.return_value)
        self.mock_area.__contains__.assert_called_once_with(
            T.image2screen.return_value)
        self.mock_timer_instance.start_or_check.assert_called_once_with(
            patience)

    def test_time_is_after_second_frame(self):
        patience = 0.2

        T = tracker.EyeTracker('ANY_CAMERA')
        T.image2screen = mock.Mock()

        self.mock_area.__contains__.return_value = True
        self.mock_timer_instance.start_or_check.side_effect = [False, True]

        T.wait_for_fixation(self.mock_area, patience)

        self.assertEqual(len(self.mock_i2pos.mock_calls), 2)
        self.assertEqual(len(T.image2screen.mock_calls), 2)
        self.assertEqual(len(self.mock_area.__contains__.mock_calls), 2)
        self.assertEqual(
            len(self.mock_timer_instance.start_or_check.mock_calls), 2)

    def test_point_not_in_area(self):
        T = tracker.EyeTracker('ANY_CAMERA')
        T.image2screen = mock.Mock()

        self.mock_area.__contains__.return_value = False

        T.wait_for_fixation(self.mock_area, 0.2)

        self.assertEqual(len(self.mock_timer_instance.clear.mock_calls), 2)


class TestTrackerCalibrate(TestCase):

    def setUp(self):
        self.mock_queue = mock.patch('vyu.tracker.Queue').start()
        self.mock_process = mock.patch('vyu.tracker.Process').start()
        self.mock_get_reader = mock.patch(
            'vyu.tracker.imageio.get_reader').start()
        self.mock_estimate_matrices = mock.patch(
            'vyu.tracker.calibration.estimate_matrices').start()
        self.mock_estimate_matrices.return_value = ('ANY_MATRIX', 'ANY_VECTOR')
        self.mock_kill = mock.patch('vyu.tracker.os.kill').start()

        self.tracker = tracker.EyeTracker()

    def tearDown(self):
        mock.patch.stopall()

    def test_enter_starts_collector_process(self):
        mock_process_instance = self.mock_process.return_value

        with self.tracker.calibrate():
            self.mock_process.assert_called_once_with(
                target=tracker.collect_frames,
                args=(self.mock_get_reader.return_value,
                      self.mock_queue.return_value))
            mock_process_instance.start.assert_called_once_with()

    def test_exit_stops_collector_process_and_kills(self):
        mock_process_instance = self.mock_process.return_value

        with self.tracker.calibrate():
            mock_process_instance.terminate.assert_not_called()
        mock_process_instance.terminate.assert_called_once_with()
        self.mock_kill.assert_called_once_with(mock_process_instance.pid,
                                               signal.SIGKILL)

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
        self.mock_get_reader = mock.patch('vyu.tracker.imageio.get_reader',
                                          mock.MagicMock()).start()
        self.mock_image2position = mock.patch(
            'vyu.tracker.image2position').start()

    def tearDown(self):
        mock.patch.stopall()

    def test_current_eye_position_gets_frame_from_reader(self):
        mock_reader = self.mock_get_reader.return_value
        mock_reader.__iter__.return_value = ['frame1', 'frame2']
        self.mock_image2position.return_value = (1, 1)

        T = tracker.EyeTracker()

        x, y = T.current_eye_position

        self.assertEqual(x, 1)
        self.assertEqual(y, 1)

        self.mock_image2position.assert_called_once_with('frame1')


class TestCollectFrames(TestCase):

    @mock.patch('vyu.tracker.image2position')
    def test_collect_frames_puts_image_position_to_queue(self, mock_i2pos):
        mock_reader = mock.MagicMock()
        mock_queue = mock.Mock()
        mock_reader.__iter__.return_value = ['frame1', 'frame2']

        tracker.collect_frames(mock_reader, mock_queue)

        self.assertEqual(mock_i2pos.call_count, 2)
        mock_i2pos.assert_has_calls([mock.call('frame1'),
                                     mock.call('frame2')])
        mock_queue.put.assert_has_calls([mock.call(mock_i2pos.return_value)]*2)
