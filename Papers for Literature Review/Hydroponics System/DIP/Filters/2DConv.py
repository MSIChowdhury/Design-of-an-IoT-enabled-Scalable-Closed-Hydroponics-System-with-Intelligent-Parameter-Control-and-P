#Averaging Blurring

import cv2
import numpy as np
from matplotlib import pyplot as plt

img = cv2.imread('test.png')
cv2.imshow("Image", img)
cv2.waitKey(0)

kernel1 = np.ones((3,3),np.float32)/9
print(kernel1)

kernel2 = np.array([[-1, -1, -1],
                    [-1, 8, -1],
                    [-1, -1, -1]])

kernel3 = np.array([[0, -1, 0],
                    [-1, 5, -1],
                    [0, -1, 0]])

kernel4 = np.array([[1, 4, 6, 4, 1],
                    [4, 16, 24, 16, 4],
                    [6, 24, 36, 24, 6],
                    [4, 16, 24, 16, 4],
                    [1, 4, 6, 4, 1]])
kernel4 = kernel4/256

#box blur
avg = cv2.filter2D(img,-1,kernel1)
cv2.imshow("Averaged Image", avg)
cv2.waitKey(0)

#Gaussian blur
gaussian_avg = cv2.filter2D(img,-1,kernel4)
cv2.imshow("Gaussian Blurred Image", gaussian_avg)
cv2.waitKey(0)

#sharpening
sharp = cv2.filter2D(img,-1,kernel3)
cv2.imshow("Sharpened Image", sharp)
cv2.waitKey(0)


#Edge detection
edg = cv2.filter2D(avg,-1,kernel2)
cv2.imshow("Edge Image", edg)
cv2.waitKey(0)




# plt.subplot(1, 2, 1)
# plt.imshow(img)
# plt.subplot(1, 2, 2)
# plt.imshow(dst)
#
# plt.show()
#
# plt.subplot(121)
# plt.imshow(img),plt.title('Original')
# plt.xticks([]), plt.yticks([])
# plt.subplot(122),plt.imshow(dst),plt.title('Averaging')
# plt.xticks([]), plt.yticks([])
# plt.show()