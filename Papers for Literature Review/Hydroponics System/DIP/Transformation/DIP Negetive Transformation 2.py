
#Name: Mikdam-Al-Maad Ronoue
import cv2
import matplotlib.pyplot as plt

img = cv2.imread("input.png")
# img = cv2.imread("memo1.jpg")
# img = cv2.imread("grayscale.png")
# cv2.imshow("Pic",img)

img_not = cv2.bitwise_not(img)
# cv2.imshow("Invert1",img_not)
cv2.imwrite("InvertedImage.png",img_not)

plt.subplot(1, 2, 1)
plt.imshow(img)
plt.subplot(1, 2, 2)
plt.imshow(img_not)

plt.show()
