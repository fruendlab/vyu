import pylab as pl
import imageio

from vyu.image import image2position


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
