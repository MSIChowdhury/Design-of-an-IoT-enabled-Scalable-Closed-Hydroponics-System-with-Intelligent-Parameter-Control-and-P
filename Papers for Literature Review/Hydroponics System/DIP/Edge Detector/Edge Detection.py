
# Python program to  Edge detection  
# using OpenCV in Python 
# using Sobel edge detection  
# and laplacian method 
import cv2 
import numpy as np 
from matplotlib import pyplot as plt

#Capture livestream video content from camera 0 
cap = cv2.VideoCapture(0) 
  
while(1): 
  
    # Take each frame 
    _, frame = cap.read() 
      
    # Convert to HSV for simpler calculations 
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) 

    # remove noise
    img = cv2.GaussianBlur(gray,(5,5),0)
      
    # Calcution of Sobelx 
    sobelx = cv2.Sobel(img,cv2.CV_64F,1,0,ksize=3) 
      
    # Calculation of Sobely 
    sobely = cv2.Sobel(img,cv2.CV_64F,0,1,ksize=3) 
  
    # Calculation of Laplacian 
    laplacian = cv2.Laplacian(img,cv2.CV_64F) 

    canny = cv2.Canny(img,3,50,200)
    
    cv2.imshow('image',gray)   
    cv2.imshow('sobelx',sobelx) 
    cv2.imshow('canny',canny) 
    cv2.imshow('laplacian',laplacian) 
	
    
    k = cv2.waitKey(5) & 0xFF
    if k == 27: 
        break
  
cv2.destroyAllWindows() 
  
#release the frame 
cap.release() 
