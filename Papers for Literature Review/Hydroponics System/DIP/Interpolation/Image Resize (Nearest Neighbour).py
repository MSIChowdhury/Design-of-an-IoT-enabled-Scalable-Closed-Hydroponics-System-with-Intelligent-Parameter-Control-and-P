import numpy as np
import cv2

def ResizeNearestNeighbour(img, resized_height, resized_width):
    height, width, channels = img.shape
    empty_image = np.zeros((resized_height, resized_width, channels), np.uint8)

    height_ratio = resized_height / height
    width_ratio = resized_width / width

    for i in range(resized_height):
        for j in range(resized_width):

            x = int(i / height_ratio)
            y = int(j / width_ratio)

            empty_image[i, j] = img[x, y]



    cv2.imshow('Resized Image', empty_image)
    cv2.imwrite('Resized Image Nearest Neighbour.jpg', empty_image)
    cv2.waitKey(0)


img = cv2.imread("ironman.jpg")
cv2.imshow('ironman', img)
cv2.waitKey(0)
ResizeNearestNeighbour(img, 419*2,236*2 )