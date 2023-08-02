import numpy as np
import cv2
import math

def bicubicFunction(a,b,c,d,x):
    val = (a*(x**3)) + (b*(x**2)) + c*x + d
    for i in range(len(val)):
        if val[i] <0:
            val[i] = 0
        elif val[i] > 255:
            val[i] = 255
    return val


def slope(x_old,y_old,x_new,y_new, channels):
    l = np.array([])
    for i in range(channels):
        y_diff = float(y_new[i]) - float(y_old[i])
        x_diff = x_new-x_old
        slp = y_diff / x_diff
        l = np.append(l,slp)
    return l


def BicubicInterpolation(image, resized_height, resized_width):

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
                # print("original",empty_image[i, j])

            else:
                y_down = int(y)
                y_up = math.ceil(y)
                if y_up >= width: y_up = y_down
                y_up_next = y_up + 1
                if y_up_next >= width:
                    y_up_next = y_up

                f_0 = image[x,y_down]
                f_1 = image[x,y_up]

                if y_down == 0:
                    f_0_derivitive = slope(y_down -1 , image[x, y_down], y_up, image[x, y_up],channels)
                else:
                    f_0_derivitive = slope(y_down - 1, image[x, y_down-1], y_up, image[x, y_up], channels)

                if y_up==width-1:
                    f_1_derivitive = slope(y_down, image[x, y_down], y_up+1, image[x, y_up],channels)
                else:
                    f_1_derivitive = slope(y_down, image[x, y_down], y_up+1, image[x, y_up+1], channels)

                a = np.array([])
                b = np.array([])
                c = np.array([])
                d = np.array([])
                for k in range(channels):
                    a_temp = (2*float(f_0[k])) - (2*float(f_1[k])) + float(f_0_derivitive[k]) + float(f_1_derivitive[k])
                    b_temp = (-3*float(f_0[k])) + (3*float(f_1[k])) - (2*float(f_0_derivitive[k])) - float(f_1_derivitive[k])
                    c_temp = float(f_0_derivitive[k])
                    d_temp = float(f_0[k])
                    a = np.append(a,a_temp)
                    b = np.append(b,b_temp)
                    c = np.append(c,c_temp)
                    d = np.append(d,d_temp)

                pixel_value = bicubicFunction(a,b,c,d,(y-y_down))


                empty_image[i, j] = pixel_value
                # print(i,j)
                # print(f_0,empty_image[i,j],f_1)
                # print(f_0_derivitive,f_1_derivitive)
                # print(a,b,c,d)
        # cv2.imshow("a",empty_image)
        # cv2.waitKey(0)
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
                x_up_next = x_up + 1
                if x_up_next >= height:
                    x_up_next = x_up

                f_0 = empty_image[x_down,y]
                f_1 = empty_image[x_up,y]

                if x_down == 0:
                    f_0_derivitive = slope(x_down -1 , empty_image[x_down, y], x_up, empty_image[x_up, y],channels)
                else:
                    f_0_derivitive = slope(x_down - 1, empty_image[x_down-1, y], x_up, empty_image[x_up, y], channels)

                if x_up==height-1:
                    f_1_derivitive = slope(x_down, empty_image[x_down, y], x_up+1, empty_image[x_up, y],channels)
                else:
                    f_1_derivitive = slope(x_down, empty_image[x_down, y], x_up+1, empty_image[x_up+1, y], channels)

                a = np.array([])
                b = np.array([])
                c = np.array([])
                d = np.array([])
                for k in range(channels):
                    a_temp = (2*float(f_0[k])) - (2*float(f_1[k])) + float(f_0_derivitive[k]) + float(f_1_derivitive[k])
                    b_temp = (-3*float(f_0[k])) + (3*float(f_1[k])) - (2*float(f_0_derivitive[k])) - float(f_1_derivitive[k])
                    c_temp = float(f_0_derivitive[k])
                    d_temp = float(f_0[k])
                    a = np.append(a,a_temp)
                    b = np.append(b,b_temp)
                    c = np.append(c,c_temp)
                    d = np.append(d,d_temp)

                pixel_value = bicubicFunction(a,b,c,d,(x-x_down))


                empty_image_2[i, j] = pixel_value


    return empty_image_2


img = cv2.imread("ironman.jpg")
cv2.imshow('ironman', img)


resized_image = BicubicInterpolation(img,  419*2, 236*2 )
cv2.imshow('Resized Image ', resized_image)
cv2.imwrite('Resized Image Bicubic Interpolation.jpg', resized_image)
cv2.waitKey(0)




