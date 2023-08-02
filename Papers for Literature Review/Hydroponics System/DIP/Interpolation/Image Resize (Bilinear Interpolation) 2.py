import numpy as np
import cv2
import math


def BilinearInterpolation(image, resized_height, resized_width):

    height, width, channels = image.shape
    print(height, width, channels)
    empty_image = np.zeros((height, resized_width, channels), np.uint8)
    empty_image_2 = np.zeros((resized_height, resized_width, channels), np.uint8)


    height_ratio = resized_height / height
    width_ratio = resized_width / width

    for i in range(height):
        for j in range(resized_width):
            x = i
            y = j/width_ratio

            if y.is_integer():
                x = int(x)
                y = int(y)
                empty_image[i, j] = image[x, y]
            else:
                y_down = int(y)
                y_up = math.ceil(y)
                if y_up >= width: y_up = y_down
                y_down_weight = y - y_down
                y_up_weight = y_up - y

                empty_image[i, j] = image[x, y_down] * (1-y_down_weight) + image[x, y_up] * (1-y_up_weight)
                # print(empty_image[i,j])

    for j in range(resized_width):
        for i in range(resized_height):
            x = i / height_ratio
            y = j

            if x.is_integer() :
                x = int(x)
                y = int(y)

                empty_image_2[i, j] = empty_image[x, y]

            else:
                x_down = int(x)
                x_up = math.ceil(x)
                if x_up >= height: x_up = x_down
                x_down_weight = x - x_down
                x_up_weight = x_up - x

                empty_image_2[i,j] = empty_image[x_down, y]*(1-x_down_weight) + empty_image[x_up, y]*(1-x_up_weight)

    return empty_image_2



img = cv2.imread("ironman.jpg")
cv2.imshow('ironman', img)


resized_image = BilinearInterpolation(img,  419*2, 236*2 )
cv2.imshow('Resized Image ', resized_image)
cv2.imwrite('Resized Image Bilinear Interpolation.jpg', resized_image)
cv2.waitKey(0)




