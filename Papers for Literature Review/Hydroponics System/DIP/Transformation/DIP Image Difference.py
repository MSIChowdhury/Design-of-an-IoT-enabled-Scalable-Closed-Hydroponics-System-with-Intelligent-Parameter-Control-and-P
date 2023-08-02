
#Name: Mikdam-Al-Maad Ronoue
import cv2
import math
import numpy as np
import matplotlib.pyplot as plt


def imageDifference(f,h):
    g = np.copy(f)

    for k in range(len(f)):
        diff = int(f[k]) - int(h[k])
        if diff>255:
            diff = 255
        elif diff<0:
            diff = 0
        g[k] = diff

    return g



def differenceImage(image1,image2):

    height, width, channels = image1.shape

    empty_image = np.zeros((height, width, channels), np.uint8)
    for i in range(height):
        for j in range(width):
            f = image1[i,j]
            h = image2[i,j]

            empty_image[i,j] = imageDifference(f,h)

    return empty_image


# Read the original image
img1 = cv2.imread("PowerLawTransformedImage.png")
img2 = cv2.imread("Result4.png")
differenceImage = differenceImage(img1,img2)
cv2.imwrite("differencePowerLawTransformedImage.png",differenceImage)

plt.subplot(2, 2, 1)
plt.imshow(img1)
plt.subplot(2, 2, 2)
plt.imshow(img2)
plt.subplot(2, 2, 3)
plt.imshow(differenceImage)

plt.show()

