from PIL import Image
import matplotlib.pyplot as plt
import cv2
import numpy as np

def equalization(img, L=256):

    height, width = img.shape
    MN = height * width
    intensity_count, total_values_used = np.histogram(img.flatten(), L, [0, L])
    pdf = intensity_count / MN
    cdf = pdf.cumsum()  # Calculate CDF
    equalized_intensity = np.round(cdf * (L-1))
    return equalized_intensity

def matching(original_image, empty_image, original_map, matching_map):

    height, width = original_image.shape
    for y in range(height):
        for x in range(width):
            b = original_image[y,x]
            temp  = original_map[original_image[y, x]]
            result = np.where(matching_map == temp)

            if len(result[0]) == 0:
                for i in range(1,int(temp)):
                    temp = temp - i
                    result = np.where(matching_map == temp)
                    if len(result[0]) == 0:
                        continue
                    else:
                        empty_image[y,x] = result[0][0]
                        break
            else:
                empty_image[y,x] = result[0][0]


    return empty_image

img = cv2.imread('input.png')
img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
cv2.imshow("Original", img)
matched = np.zeros(img.shape, np.uint8)
equalized_intensity1 = equalization(img)

match_img = cv2.imread("result3.png")
match_img = cv2.cvtColor(match_img, cv2.COLOR_BGR2GRAY)
cv2.imshow("Match Image", match_img)
equalized_intensity2 = equalization(match_img)

matched_img = matching(img, matched, equalized_intensity1, equalized_intensity2)
cv2.imshow("Matched Image", matched_img)
cv2.imwrite("Matched_image.png", matched_img)

print(np.array_equal(equalized_intensity1, equalized_intensity2))

cv2.waitKey(0)

cv2.destroyAllWindows()