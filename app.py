import cv2

# 1. Create a VideoCapture object. 
# The '0' argument specifies the default webcam.
# If you have multiple cameras, you might need to try '1' or '2'.
cap = cv2.VideoCapture(0)

# Check if the webcam was opened successfully
if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

# This is the main loop where we'll grab and display frames
while True:
    # 2. Read one frame from the webcam.
    # 'ret' is a boolean that is True if the frame was read successfully.
    # 'frame' is the captured image.
    ret, frame = cap.read()

    # If the frame was not captured correctly, break the loop
    if not ret:
        print("Error: Can't receive frame. Exiting ...")
        break

    # 3. Display the resulting frame
    cv2.imshow('Laptop Webcam', frame)

    # Wait for a key press. If 'q' is pressed, break the loop.
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything is done, release the capture and close all windows
cap.release()
cv2.destroyAllWindows()