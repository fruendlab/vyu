from unittest import TestCase

from vyu import area


class TestRectangle(TestCase):

    def setUp(self):
        self.rect = area.Rectangle((15, 15), (50, 50))

    def test_point_in_rectangle_should_be_true(self):
        point = (20, 40)
        self.assertTrue(point in self.rect)

    def test_point_outside_rectangle_should_be_false(self):
        point = (10, 10)
        self.assertFalse(point in self.rect)

    def test_point_left_of_rectangle_should_be_false(self):
        point = (10, 25)
        self.assertFalse(point in self.rect)

    def test_point_right_of_rectangle_should_be_false(self):
        point = (55, 25)
        self.assertFalse(point in self.rect)

    def test_point_below_rectangle_should_be_false(self):
        point = (25, 13)
        self.assertFalse(point in self.rect)

    def test_point_above_rectangle_should_be_false(self):
        point = (45, 55)
        self.assertFalse(point in self.rect)


class TestCircle(TestCase):

    def setUp(self):
        self.circle = area.Circle((0, 0), 5)

    def test_point_in_circle_should_be_true(self):
        point = (2, 2)
        self.assertTrue(point in self.circle)

    def test_point_outside_of_circle_should_be_false(self):
        point = (6, 9)
        self.assertFalse(point in self.circle)
