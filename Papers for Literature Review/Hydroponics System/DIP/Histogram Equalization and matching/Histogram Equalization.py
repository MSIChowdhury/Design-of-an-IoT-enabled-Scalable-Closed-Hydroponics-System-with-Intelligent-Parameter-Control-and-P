#Mikdam-Al-Maad Ronoue

from PIL import Image
import matplotlib.pyplot as plt
import cv2
import numpy as np


img = cv2.imread('Fig0310(a)(Moon Phobos).tif',0)
height,width = img.shape[:2]

#Printing Original Image Histogram
plt.hist(img.ravel(),256,[0,256])
plt.xlabel('Intensity Values')
plt.ylabel('Pixel Count')
plt.show()

#Histogram Equalization Operation
equ = cv2.equalizeHist(img)
cv2.imshow("Equalized", equ)
cv2.waitKey(0)
cv2.imwrite("Equalized.tif", equ)


#Equalized Image Histogram
plt.hist(equ.ravel(),256,[0,256])
plt.xlabel('Intensity Values')
plt.ylabel('Pixel Count')
plt.show()


#Generating Bimodal Distribution
from pylab import *
from scipy.optimize import curve_fit

data=concatenate((normal(40,16.25,5000),normal(240,15,350)))

y,x,_=hist(data,255,alpha=.4,label='data')
plt.close()
plt.show()

x=(x[1:]+x[:-1])/2 # for len(x)==len(y)

def gauss(x,mu,sigma,A):
    return A*exp(-(x-mu)**2/2/sigma**2)

def bimodal(x,mu1,sigma1,A1,mu2,sigma2,A2):
    return gauss(x,mu1,sigma1,A1)+gauss(x,mu2,sigma2,A2)

bimodal = bimodal(x,40,16.25,5000,180,15,350)
print(len(bimodal))
print(bimodal)
print(type(bimodal))
bimodal1 = bimodal/ 285714
print(bimodal1)
plt.plot(x,bimodal1,color='red',lw=3,label='model')
plt.xlim(0,255)
plt.ylim(-0.001,0.02)
plt.legend()
plt.title("Bimodal Gaussian Function --Specified Histogram")
plt.show()
print()

#Change intesity here to see PDF
intensity = 40
print(f"If intensity value is {intensity} PDF is {np.interp(intensity, x,bimodal1)}")
