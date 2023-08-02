import cv2
import numpy as np
from matplotlib import pyplot as plt

img = cv2.imread('Gaussian_noise_3.jpg')

blur = cv2.bilateralFilter(img,9,75,75)

cv2.imwrite("Output_bilateral_blur_3.png",blur)


plt.subplot(1, 2, 1)
plt.xticks([]), plt.yticks([])
plt.imshow(img)
plt.subplot(1, 2, 2)
plt.xticks([]), plt.yticks([])
plt.imshow(noise_free)
plt.show()