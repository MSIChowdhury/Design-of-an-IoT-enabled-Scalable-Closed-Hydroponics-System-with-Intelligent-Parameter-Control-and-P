import cv2

# Initialize the webcam
cap = cv2.VideoCapture(0)

# Check if the webcam is opened successfully
if not cap.isOpened():
    print("Error: Could not open the webcam")
    exit()

image_counter = 1  # Initialize the counter for image naming

while True:
    # Read a frame from the webcam
    ret, frame = cap.read()

    # Save the captured image with a serial name
    image_filename = f"Day_{image_counter}.jpg"
    cv2.imwrite(image_filename, frame)
    print(f"Image saved as {image_filename}")

    # Increment the counter
    image_counter += 1

    # Display the live video
    cv2.imshow("Live Video", frame)


    # Break the loop if the user presses the 'q' key
    if cv2.waitKey(1000) & 0xFF == ord('q'):
        break

# Release the webcam and close the OpenCV window
cap.release()
cv2.destroyAllWindows()
