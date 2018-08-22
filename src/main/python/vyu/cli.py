import sys
from itertools import product
import numpy as np
import matplotlib.pyplot as plt
import imageio
import time
import pygame

from vyu.image import image2position
from vyu.tracker import EyeTracker
from vyu import area


def monitor(args):
    reader = imageio.get_reader('<video{}>'.format(args['--camera']))
    w, h = next(iter(reader)).shape[:2]
    pygame.init()
    display = pygame.display.set_mode((h, w))
    running = True

    for frame in reader:
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                running = False
        x, y = image2position(frame)
        if args['--flipxy']:
            x, y = y, x

        surf = pygame.surfarray.make_surface(np.transpose(frame, (1, 0, 2)))
        circ = pygame.draw.circle(surf,
                                  pygame.Color(255, 0, 0),
                                  (int(y), int(x)),
                                  2)
        display.blit(surf, (0, 0))
        pygame.display.update()

        # print('Positon: ({:.3f}, {:.3f})'.format(y, x))
        if not running:
            break


def test(args):
    tracker = EyeTracker('<video{}>'.format(args['--camera']))

    pygame.init()
    display = pygame.display.set_mode((800, 800))

    # First calibrate
    calibration_positions = list(product([100, 200, 300], [100, 200, 300]))
    with tracker.calibrate() as C:
        for x, y in calibration_positions:
            surf = pygame.surfarray.make_surface(np.zeros((400, 400)))
            circ = pygame.draw.circle(surf,
                                      pygame.Color(255, 0, 0),
                                      (int(x), int(y)),
                                      2)
            display.blit(surf, (200, 200))
            pygame.display.update()

            running = True
            while running:
                time.sleep(0.05)
                for event in pygame.event.get():
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        running = False

            C.append((x, y))

    # Show target and wait
    surf = pygame.surfarray.make_surface(np.zeros((400, 400)))
    circ = pygame.draw.circle(surf,
                              pygame.Color(255, 0, 0),
                              (250, 250),
                              2)
    display.blit(surf, (200, 200))
    pygame.display.update()

    def callback(centroid):
        surf = pygame.surfarray.make_surface(np.zeros((400, 400)))
        circ = pygame.draw.circle(surf,
                                  pygame.Color(255, 0, 0),
                                  (250, 250),
                                  2)
        eyepos = pygame.draw.circle(surf,
                                    pygame.Color(0, 0, 255),
                                    (int(centroid[0]), int(centroid[1])),
                                    2)
        display.blit(surf, (200, 200))
        pygame.display.update()


    try:
        tracker.wait_for_fixation(area.Circle((250, 250), 20), patience=0.4, log=True, timeout=20, callback=callback)
        print('Fixation in the correct location')
    except:
        print('Exception')
        pass
    tracker.stop()
