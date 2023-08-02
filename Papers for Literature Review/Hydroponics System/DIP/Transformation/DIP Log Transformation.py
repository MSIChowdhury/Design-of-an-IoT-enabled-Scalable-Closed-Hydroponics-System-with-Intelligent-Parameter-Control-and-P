
#Name: Mikdam-Al-Maad Ronoue
import cv2
import math
import numpy as np
import matplotlib.pyplot as plt

def logTransform(c, f):
    g = np.copy(f)
    for k in range(len(f)):
        g[k] = round(c * math.log(float(1 + f[k])))
    return g



def logTransformImage(image, outputMax=255, inputMax=255):

    inputMax = np.max(image)
    c = outputMax / math.log(inputMax + 1)



    height, width, channels = image.shape

    empty_image = np.zeros((height, width, channels), np.uint8)
    for i in range(height):
        for j in range(width):
            f = image[i,j]

            empty_image[i,j] = logTransform(c, f)

    return empty_image


# Read the original image
img = cv2.imread("input.png")

logTransformedImage = logTransformImage(img)
cv2.imwrite("logTransformedImage.png",logTransformedImage)

plt.subplot(1, 2, 1)
plt.imshow(img)
plt.subplot(1, 2, 2)
plt.imshow(logTransformedImage)

plt.show()
