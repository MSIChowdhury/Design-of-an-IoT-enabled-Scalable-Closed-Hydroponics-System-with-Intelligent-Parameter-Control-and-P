import numpy as np
import os
import cv2
import matplotlib.pyplot as plt


# defining the canny detector function

# here weak_th and strong_th are thresholds for
# double thresholding step
def Canny_detector(img, weak_th=None, strong_th=None):
    # conversion of image to grayscale
    img = cv2.resize(img, (400, 400), interpolation = cv2.INTER_AREA)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    cv2.imshow('Grayscale', img)
    cv2.imwrite("Grayscale.jpg", img)

    # Noise reduction step
    img = cv2.GaussianBlur(img, (5, 5), 1)
    cv2.imshow('Noise Reduction', img)
    cv2.imwrite("Noise Reduction.jpg", img)

    # Calculating the gradients
    gx = cv2.Sobel(np.float32(img), cv2.CV_64F, 1, 0, 3)
    gy = cv2.Sobel(np.float32(img), cv2.CV_64F, 0, 1, 3)
    print("gx = ", gx)
    print("gy = ", gy)

    # Conversion of Cartesian coordinates to polar
    mag, ang = cv2.cartToPolar(gx, gy, angleInDegrees=True)
    print("Magnitude = ", mag)
    print("Angle = ", ang)

    # setting the minimum and maximum thresholds
    # for double thresholding
    mag_max = np.max(mag)
    print("Maximum magnitude = ", mag_max)

    if not weak_th: weak_th = mag_max * 0.1
    if not strong_th: strong_th = mag_max * 0.7

    # getting the dimensions of the input image
    height, width = img.shape

    # Looping through every pixel of the grayscale
    # image
    # for i_x in range(width):
    #     for i_y in range(height):
    #
    #         grad_ang = ang[i_y, i_x]
    #         grad_ang = abs(grad_ang - 180) if abs(grad_ang) > 180 else abs(grad_ang)
    #
    #         # selecting the neighbours of the target pixel
    #         # according to the gradient direction
    #         # In the x axis direction
    #         if grad_ang <= 22.5:
    #             neighb_1_x, neighb_1_y = i_x - 1, i_y
    #             neighb_2_x, neighb_2_y = i_x + 1, i_y
    #
    #         # top right (diagnol-1) direction
    #         elif grad_ang > 22.5 and grad_ang <= (22.5 + 45):
    #             neighb_1_x, neighb_1_y = i_x - 1, i_y - 1
    #             neighb_2_x, neighb_2_y = i_x + 1, i_y + 1
    #
    #         # In y-axis direction
    #         elif grad_ang > (22.5 + 45) and grad_ang <= (22.5 + 90):
    #             neighb_1_x, neighb_1_y = i_x, i_y - 1
    #             neighb_2_x, neighb_2_y = i_x, i_y + 1
    #
    #         # top left (diagnol-2) direction
    #         elif grad_ang > (22.5 + 90) and grad_ang <= (22.5 + 135):
    #             neighb_1_x, neighb_1_y = i_x - 1, i_y + 1
    #             neighb_2_x, neighb_2_y = i_x + 1, i_y - 1
    #
    #         # Now it restarts the cycle
    #         elif grad_ang > (22.5 + 135) and grad_ang <= (22.5 + 180):
    #             neighb_1_x, neighb_1_y = i_x - 1, i_y
    #             neighb_2_x, neighb_2_y = i_x + 1, i_y
    #
    #         # Non-maximum suppression step
    #         if width > neighb_1_x >= 0 and height > neighb_1_y >= 0:
    #             if mag[i_y, i_x] < mag[neighb_1_y, neighb_1_x]:
    #                 mag[i_y, i_x] = 0
    #                 continue
    #
    #         if width > neighb_2_x >= 0 and height > neighb_2_y >= 0:
    #             if mag[i_y, i_x] < mag[neighb_2_y, neighb_2_x]:
    #                 mag[i_y, i_x] = 0
    #
    #
    # cv2.imshow("Non-maximum Suppression", mag)
    # cv2.imwrite("Non-maximum Suppression.jpg", mag)


    # # weak_ids = np.zeros_like(img)
    # # strong_ids = np.zeros_like(img)
    # ids = np.zeros_like(img)

    # double thresholding step
    for i_x in range(width):
        for i_y in range(height):

            grad_mag = mag[i_y, i_x]

            if grad_mag < weak_th:
                mag[i_y, i_x] = 0
            elif grad_mag >= strong_th:
                mag[i_y, i_x] = 255


    def hysteresis(img, weak, strong=255):
        M, N = img.shape
        for i in range(1, M - 1):
            for j in range(1, N - 1):
                if (img[i, j] == weak):
                    try:
                        if ((img[i + 1, j - 1] == strong) or (img[i + 1, j] == strong) or (img[i + 1, j + 1] == strong)
                                or (img[i, j - 1] == strong) or (img[i, j + 1] == strong)
                                or (img[i - 1, j - 1] == strong) or (img[i - 1, j] == strong) or (
                                        img[i - 1, j + 1] == strong)):
                            img[i, j] = strong
                        else:
                            img[i, j] = 0
                    except IndexError as e:
                        pass
        return img

    hysteresis_img =  hysteresis(mag, weak_th)


    cv2.imshow("Double Thresholding", mag)
    # cv2.imwrite("Double Thresholding.jpg", mag)
    cv2.imshow("Hysteresis", hysteresis_img)
    # cv2.imwrite("Hysteresis.jpg", hysteresis_img)

    # finally returning the magnitude of
    # gradients of edges
    return hysteresis_img


img = cv2.imread("rubicks3.jpg")
img = cv2.resize(img, (400, 400), interpolation = cv2.INTER_AREA)
cv2.imwrite("input.jpg", img)
canny_img = Canny_detector(img)
cv2.imshow("original", img)
cv2. imshow("canny_output",canny_img)
cv2.imwrite("output 2(b).jpg",canny_img)


if cv2.waitKey(0) & 0xFF == 27:
    cv2.destroyAllWindows()

