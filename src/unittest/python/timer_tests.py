from unittest import TestCase, mock

from vyu import timer


class TimerTests(TestCase):

    @mock.patch('vyu.timer.time.time')
    def test_starts_timer(self, mock_time):
        t = timer.Timer()
        t.start()
        self.assertEqual(t.t0, mock_time.return_value)
        mock_time.assert_called_once_with()

    def test_timer_is_not_running_when_intialized(self):
        t = timer.Timer()
        self.assertFalse(t.isrunning())

    @mock.patch('vyu.timer.time.time')
    def test_timer_is_running_when_started(self, mock_time):
        t = timer.Timer()
        t.start()
        self.assertTrue(t.isrunning())

    @mock.patch('vyu.timer.time.time')
    def test_timer_is_not_running_after_clear(self, mock_time):
        t = timer.Timer()
        t.start()
        t.clear()
        self.assertFalse(t.isrunning())

    @mock.patch('vyu.timer.time.time')
    def test_time_when_time_is_up(self, mock_time):
        mock_time.side_effect = [1, 5]
        t = timer.Timer()
        t.start()
        self.assertTrue(t.check_time(2))

    @mock.patch('vyu.timer.time.time')
    def test_time_when_time_is_not_up_yet(self, mock_time):
        mock_time.side_effect = [1, 2]
        t = timer.Timer()
        t.start()
        self.assertFalse(t.check_time(2))

    def test_start_or_check_if_not_running(self):
        t = timer.Timer()
        t.isrunning = mock.Mock()
        t.start = mock.Mock()
        t.check_time = mock.Mock()

        t.isrunning.return_value = False

        self.assertEqual(t.start_or_check(0.2), t.check_time.return_value)

        t.start.assert_called_once_with()

    def test_start_or_check_if_running(self):
        t = timer.Timer()
        t.isrunning = mock.Mock()
        t.start = mock.Mock()
        t.check_time = mock.Mock()

        t.isrunning.return_value = True

        self.assertEqual(t.start_or_check(0.2), t.check_time.return_value)

        t.start.assert_not_called()
