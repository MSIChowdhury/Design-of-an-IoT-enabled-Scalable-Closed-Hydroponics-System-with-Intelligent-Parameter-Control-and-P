
#Name: Mikdam-Al-Maad Ronoue
import cv2
import math
import numpy as np
import matplotlib.pyplot as plt


c = 1
gamma = float(input("input gamma :"))
def PowerLawTransform(c, f, min, max):
    g = np.copy(f)
    for k in range(len(f)):
        temp = c* (int(f[k]**gamma))
        temp = (temp-min)/(max-min)
        temp = temp*255
        g[k] = temp
    return g



def PowerLawTransformImage(image,c):

    height, width, channels = image.shape
    minimum = np.infty
    maximum = 0

    for i in range(height):
        for j in range(width):
            for k in range(channels):
                s = (c * (image[i][j][k])**gamma)
                if (s > maximum):
                    maximum = s
                if (s < minimum):
                    minimum = s

    empty_image = np.zeros((height, width, channels), np.uint8)
    for i in range(0, height):
        for j in range(0, width):
            f = image[i,j]

            empty_image[i,j] = PowerLawTransform(c,f,minimum,maximum)

    return empty_image


# Read the original image
img = cv2.imread("input.png")

PowerLawTransformedImage = PowerLawTransformImage(img,c)
#cv2.imwrite("PowerLawTransformedImage.png",PowerLawTransformedImage)

plt.subplot(1, 2, 1)
plt.imshow(img)
plt.subplot(1, 2, 2)
plt.imshow(PowerLawTransformedImage)

plt.show()
