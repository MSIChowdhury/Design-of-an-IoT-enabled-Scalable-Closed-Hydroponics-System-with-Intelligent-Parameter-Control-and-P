import cv2
import numpy as np
from matplotlib import pyplot as plt

img = cv2.imread('Salt_pepper_2.png')

noise_free = cv2.medianBlur(img,5)
cv2.imwrite("Output_median_blur.png",noise_free)


plt.subplot(1, 2, 1)
plt.xticks([]), plt.yticks([])
plt.imshow(img)
plt.subplot(1, 2, 2)
plt.xticks([]), plt.yticks([])
plt.imshow(noise_free)
plt.show()
