#RME 4112 Assignment - 07
#Date of submission: 27th March, 2023
#Group A
#Members: MD. Sameer Iqbal Chowdhury (Class Roll: SH-092-002)
#         Mikdam-Al-Maad Ronoue (Class Roll: FH-092-003)
#         Tapos Biswas (Class Roll: JN-092-004)

##The code starts here##

import cv2
import numpy as np

def plate_detection(img):
    # Convert the image to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    filtered_img = cv2.medianBlur(gray, 3)
    _, thresholded_img = cv2.threshold(gray, 115, 255, cv2.THRESH_BINARY)

    kernel = np.ones((3,3), np.uint8)
    dilated_img = cv2.dilate(thresholded_img, kernel, iterations=1)
    edge = dilated_img - thresholded_img

    # Dilate the image
    dilation = cv2.dilate(edge, kernel, iterations=1)

    # Erode the dilated image
    erosion = cv2.erode(dilation, kernel, iterations=1)

    contours, hierarchy = cv2.findContours(erosion, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        aspect_ration = float(w)/h
        # Loop through each connected component and draw its bounding box on the original image
        if aspect_ration > 2 and w> 140 and h> 40:
            approx = cv2.approxPolyDP(cnt, 0.02 * cv2.arcLength(cnt, True), True)
            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(approx)
                print(x,y,w,h)
                rect = cv2.minAreaRect(cnt)
                box = cv2.boxPoints(rect)
                box = np.int0(box)
                cv2.drawContours(img, [box], 0, (0, 0, 255), 2)
                img_plate = img[y:y + h, x:x + w]
                cv2.imshow('Finding license plate', img)
                cv2.imwrite("Identification_license_plate.jpg",img)
                cv2.waitKey(0)
                cv2.imshow('License Plate', img_plate)
                cv2.imwrite("License_Plate.jpg",img_plate)
                cv2.waitKey(0)
    return img_plate



def text_detection(img):
    gray = cv2.cvtColor(license_plate, cv2.COLOR_BGR2GRAY)

    filtered_img = cv2.medianBlur(gray, 3)
    _, thresholded_img = cv2.threshold(gray, 80, 255, cv2.THRESH_BINARY)

    kernel = np.ones((3, 3), np.uint8)
    kernel2 = np.ones((3,2), np.uint8)
    dilated_img = cv2.dilate(thresholded_img, kernel, iterations=1)
    edge = dilated_img - thresholded_img

    # # edge2 = cv2.erode(edge, kernel2, iterations=1)
    edge2 = cv2.dilate(edge, kernel2, iterations=1)
    # closing = cv2.morphologyEx(edge, cv2.MORPH_CLOSE, kernel2)
    #
    # Create a rectangular structuring element
    se = cv2.getStructuringElement(cv2.MORPH_RECT, (2,2))

    # Apply morphological closing to fill holes in the binary image
    closing = cv2.morphologyEx(edge2, cv2.MORPH_CLOSE, se)

    text_img = cv2.morphologyEx(closing, cv2.MORPH_OPEN, se)

    cv2.imshow('plate', text_img)
    cv2.imwrite("plate.jpg", text_plate)
    cv2.waitKey(0)




# Load the color image
img = cv2.imread('car4.jpg')
license_plate = plate_detection(img)
text_detection(license_plate)
cv2.destroyAllWindows()


