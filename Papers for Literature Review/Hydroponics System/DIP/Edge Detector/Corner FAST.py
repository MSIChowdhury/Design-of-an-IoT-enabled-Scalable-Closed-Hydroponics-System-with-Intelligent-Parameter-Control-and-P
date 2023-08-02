import cv2

# Load the input image
img = cv2.imread('rubicks3.jpg')

# Convert the image to grayscale
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Set FAST parameters
fast = cv2.FastFeatureDetector_create(threshold=50)

# Detect corners using FAST algorithm
keypoints = fast.detect(gray, None)

# Draw detected corners on the input image
img_with_corners = cv2.drawKeypoints(img, keypoints, None, color=(0, 0, 255))

# Display the output image
cv2.imshow('FAST corners', img_with_corners)
cv2.imwrite("FASTcorners.jpg", img_with_corners)
cv2.waitKey(0)
cv2.destroyAllWindows()
