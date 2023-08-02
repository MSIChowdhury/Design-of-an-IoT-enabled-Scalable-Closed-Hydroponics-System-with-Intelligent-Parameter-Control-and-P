import cv2
import numpy as np

# Load the two images and the mask
image1 = cv2.imread('ironman.png')
image1 = np.asarray(image1, np.uint8)
image2 = cv2.imread('hulk.png')
image2 = np.asarray(image2, np.uint8)
mask = cv2.imread('mask.png')
mask = np.asarray(mask, np.uint8)

height, width, channels = image1.shape
print(height, width)
image2 = cv2.resize(image2,(width, height))
mask = cv2.resize(mask, (width, height))

# Normalize the mask to be between 0 and 1
mask = mask / 255
mask = np.asarray(mask, np.uint8)
print(mask)

# Multiply the images by the mask
image1_masked = cv2.multiply(image1, mask)

image2_masked = cv2.multiply(image2, 1 - mask)

# Add the masked images together
combined_image = cv2.add(image1_masked, image2_masked)

# Display the result
cv2.imwrite("Ironman_Hulk.png",combined_image)
cv2.imshow('Combined Image', combined_image)
cv2.waitKey(0)
cv2.destroyAllWindows()
