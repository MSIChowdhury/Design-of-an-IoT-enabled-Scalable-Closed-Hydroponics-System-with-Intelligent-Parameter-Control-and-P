
#Name: Mikdam-Al-Maad Ronoue
import cv2
import math
import numpy as np
import matplotlib.pyplot as plt


def contrastStretching(f):
    g = np.copy(f)
    min_range = 105
    max_range = 175
    for k in range(len(f)):
        if f[k]<=min_range:
            temp = 0
            g[k] = temp
        elif f[k]>min_range and f[k]<max_range:
            temp = 255 * (f[k]-min_range)/(max_range-min_range)
            g[k] = temp

        else:
            temp = 255
            g[k] = temp

    return g



def contrastStretchedImage(image):

    height, width, channels = image.shape
    minimum = np.min(image)
    maximum = np.max(image)

    empty_image = np.zeros((height, width, channels), np.uint8)
    for i in range(0, height):
        for j in range(0, width):
            f = image[i,j]

            empty_image[i,j] = contrastStretching(f)

    return empty_image


# Read the original image
img = cv2.imread("input.png")
contrastStretchedImage = contrastStretchedImage(img)
cv2.imwrite("contrastStretchedImage.png",contrastStretchedImage)

plt.subplot(1, 2, 1)
plt.imshow(img)
plt.subplot(1, 2, 2)
plt.imshow(contrastStretchedImage)

plt.show()

