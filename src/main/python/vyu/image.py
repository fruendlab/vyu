import numpy as np
from scipy.ndimage import label
from skimage.color import rgb2gray


def image2position(img, thres=0.5):
    grayscale_img = rgb2gray(img)
    x, y = get_brightest_point(grayscale_img)
    thresholded = threshold_image(grayscale_img, thres)
    connected_clusters, _ = label(thresholded)
    centroid = get_centroid(connected_clusters == connected_clusters[x, y])
    return centroid


def get_brightest_point(grayscale_img):
    return np.unravel_index(np.argmax(grayscale_img), grayscale_img.shape)


def threshold_image(grayscale_img, thres):
    return grayscale_img > thres


def get_centroid(region):
    xvals, yvals = np.where(region)
    return xvals.mean(), yvals.mean()
