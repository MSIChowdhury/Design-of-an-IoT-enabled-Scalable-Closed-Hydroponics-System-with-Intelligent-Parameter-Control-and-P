from PIL import Image
import matplotlib.pyplot as plt
import cv2
import numpy as np

img = cv2.imread('Fig0310(a)(Moon Phobos).tif')

img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

height, width = img.shape
MN = height * width

equalized= np.zeros(img.shape, np.uint8)

L = 256

intensity_count, total_values_used = np.histogram(img.flatten(), L, [0, L])

pdf = intensity_count / MN

cdf = pdf.cumsum()  # Calculate CDF

equalized_intensity = np.round(cdf * (L-1))

for y in range(height):
    for x in range(width):
        # Apply the new intensities in our new image
        equalized[y, x] = equalized_intensity[img[y, x]]


cv2.imshow("a", equalized)
cv2.imwrite("New Equlized Scratch Image.png", equalized)

plt.hist(img.ravel(), 256, [0, 256])
plt.xlabel('Intensity Values')
plt.ylabel('Pixel Count')
plt.show()

plt.hist(equalized.ravel(), 256, [0, 256])
plt.xlabel('Intensity Values')
plt.ylabel('Pixel Count')
plt.show()

cv2.waitKey(0)

cv2.destroyAllWindows()