import pylab as pl
import imageio
import time

from vyu.image import image2position
from vyu.tracker import EyeTracker
from vyu import area


class KeyMonitor(object):

    def __init__(self):
        self.stop_loop = False

    def key_pressed(self, event):
        self.stop_loop = True


def monitor(args):
    reader = imageio.get_reader('<video{}>'.format(args['--camera']))

    fig = pl.figure(figsize=[float(x) for x in args['--size'].split('x')])
    ax = fig.add_subplot(111)
    pl.setp(ax, frame_on=False, xticks=(), yticks=())
    eyemonitor = ax.imshow(next(iter(reader)))
    position_marker = ax.plot([0], [0], '.', color='magenta')
    fig.show()
    eyemonitor.axes.figure.canvas.draw()

    key_monitor = KeyMonitor()
    fig.canvas.mpl_connect('key_press_event', key_monitor.key_pressed)

    for frame in reader:
        x, y = image2position(frame)
        if args['--flipxy']:
            x, y = y, x

        eyemonitor.set_data(frame)
        pl.setp(position_marker, xdata=[y], ydata=[x])

        eyemonitor.axes.figure.canvas.draw()
        position_marker[0].axes.figure.canvas.draw()  # do we need this?

        print('Positon: ({:.3f}, {:.3f})'.format(y, x))

        if key_monitor.stop_loop:
            break


def test(args):
    tracker = EyeTracker('<video{}>'.format(args['--camera']))

    fig = pl.figure()
    ax = fig.add_subplot(111)
    pl.setp(ax, frame_on=False,
            xticks=(), yticks=(),
            xlim=(-5, 5), ylim=(-5, 5))
    fixation_target = ax.plot([0], [0], '.', color='magenta')[0]
    fig.show()
    fixation_target.axes.figure.canvas.draw()

    key_monitor = KeyMonitor()
    fig.canvas.mpl_connect('key_press_event', key_monitor.key_pressed)

    # First calibrate
    calibration_positions = [(2, 2), (-2, 2), (-2, -2), (2, -2), (0, 0)]
    with tracker.calibrate() as C:
        for x, y in calibration_positions:
            fixation_target.set_xdata(x)
            fixation_target.set_ydata(y)
            fixation_target.axes.figure.canvas.draw()

            key_monitor.stop_loop = False
            while not key_monitor.stop_loop:
                time.sleep(0.05)

            C.append((x, y))

    # Show target and wait
    fixation_target.set_xdata(1)
    fixation_target.set_ydata(1)
    fixation_target.axes.figure.canvas.draw()

    tracker.wait_for_fixation(area.Circle((1, 1), 0.5), log=True)
    print('Fixation in the correct location')
