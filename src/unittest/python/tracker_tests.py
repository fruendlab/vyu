from unittest import TestCase, mock

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
