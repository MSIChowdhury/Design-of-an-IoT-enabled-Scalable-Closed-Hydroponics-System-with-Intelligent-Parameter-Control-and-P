import cv2
import numpy as np
import math


def translation(img):
    img2 = np.zeros_like(img)
    img2[:, :-100] = img[:, 100:]

    return img2



def scaling(img):
    height, width, channels = img.shape
    xNew = int(width * 1 / 2)
    yNew = int(height * 1 / 2)
    xScale = xNew / (width - 1)
    yScale = yNew / (height - 1)
    emptyImage = np.zeros([1024, 1024, channels])

    for i in range(1024):
        for j in range(1024):
            emptyImage[i,j] = img[int(i / xScale),int(j / yScale)]


    return emptyImage

def rotation(image, degree):

    rads = math.radians(degree)


    emptyImage = np.uint8(np.zeros(image.shape))


    height = emptyImage.shape[0]
    width  = emptyImage.shape[1]

    midx,midy = (width//2, height//2)

    for i in range(emptyImage.shape[0]):
        for j in range(emptyImage.shape[1]):
            x= (i-midx)*math.cos(rads)+(j-midy)*math.sin(rads)
            y= -(i-midx)*math.sin(rads)+(j-midy)*math.cos(rads)

            x=round(x)+midx
            y=round(y)+midy

            if (x>=0 and y>=0 and x<image.shape[0] and  y<image.shape[1]):
                emptyImage[i,j,:] = image[x,y,:]

    return emptyImage



img = cv2.imread("ironman.jpg")
transformation = scaling(img)
cv2.imshow("transformed image", transformation)
cv2.imshow("image", img)
cv2.waitKey(0)

