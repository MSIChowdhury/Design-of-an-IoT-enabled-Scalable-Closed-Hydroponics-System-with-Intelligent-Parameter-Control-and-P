import cv2

cap = cv2.VideoCapture(0)
_, frame = cap.read()
cv2.imshow("Live Video", frame)
cv2.waitKey(0)
cv2.destroyAllWindows()

image_counter = 1  # Initialize the counter for image naming

def take_picture(image_counter):
    x = input("Give input: ")
    ret, frame = cap.read()
    cv2.imshow("Live Video", frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    # Save the captured image with a serial name
    image_filename = f"Day_{image_counter}.jpg"
    cv2.imwrite(image_filename, frame)


while True:
    take_picture(image_counter)
    image_counter += 1

