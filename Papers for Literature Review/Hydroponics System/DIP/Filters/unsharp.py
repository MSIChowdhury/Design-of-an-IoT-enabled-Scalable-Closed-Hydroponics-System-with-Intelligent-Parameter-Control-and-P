import numpy as np
import cv2
from matplotlib import pyplot as plt
from PIL import Image, ImageFilter
# matplotlib inline
image = cv2.imread('sample1.jpg') # reads the image
image2 = Image.fromarray(image.astype('uint8'))
new_image = image2.filter(ImageFilter.UnsharpMask(radius=2, percent=150))

plt.figure(figsize=(11,6))
plt.subplot(121),plt.imshow(image2, cmap = 'gray')
plt.title('Input Image'), plt.xticks([]), plt.yticks([])
plt.subplot(122),plt.imshow(new_image, cmap = 'gray')
plt.title('Unsharp Filter'), plt.xticks([]), plt.yticks([])
plt.show()