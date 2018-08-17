class Area(object):

    def __contains__(self, point):
        raise NotImplementedError


class Rectangle(Area):

    def __init__(self, lower_left, upper_right):
        self.left, self.low = lower_left
        self.right, self.up = upper_right

    def __contains__(self, point):
        x, y = point
        return (x >= self.left and x <= self.right and
                y >= self.low and y <= self.up)


class Circle(Area):

    def __init__(self, center, radius):
        self.center = center
        self.radius_squared = radius*radius

    def __contains__(self, point):
        squared_distance_from_center = ((self.center[0] - point[0])**2 +
                                        (self.center[1] - point[1])**2)
        return squared_distance_from_center < self.radius_squared
