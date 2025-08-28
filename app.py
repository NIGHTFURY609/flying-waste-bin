import cv2
import numpy as np

# Create a VideoCapture object for the default webcam
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

# Create the background subtractor object
backSub = cv2.createBackgroundSubtractorMOG2(history=100, varThreshold=50, detectShadows=True)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # --- FLIP THE FRAME ---
    # This line corrects the mirror effect from the webcam.
    # The '1' argument means flip horizontally.
    frame = cv2.flip(frame, 1)

    # 1. Apply the background subtractor to get the foreground mask
    fg_mask = backSub.apply(frame)

    # 2. Clean up the mask to reduce noise
    kernel = np.ones((5, 5), np.uint8)
    fg_mask = cv2.erode(fg_mask, kernel, iterations=1)
    fg_mask = cv2.dilate(fg_mask, kernel, iterations=2)

    # 3. Find contours (outlines) of the moving objects
    contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        
        if cv2.contourArea(largest_contour) > 500:
            # 4. Get the bounding box and center of the largest contour
            x, y, w, h = cv2.boundingRect(largest_contour)
            center_x = x + w // 2

            # Draw a green rectangle around the detected object
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # --- 5. Determine where the bin should move ---
            frame_width = frame.shape[1]
            zone_width = frame_width / 3
            
            command = "Stay"
            if center_x < zone_width:
                command = "Move Left"
            elif center_x > zone_width * 2:
                command = "Move Right"

            # Display the command on the screen
            cv2.putText(frame, command, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)

    # Add fallback text when no significant motion is detected
    if not contours or cv2.contourArea(largest_contour) <= 500:
        cv2.putText(frame, "No motion detected", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
        command = "Stay"

    # Display the resulting frames
    cv2.imshow('Motion Detection', frame)
    cv2.imshow('Foreground Mask', fg_mask) # You can uncomment this to see the mask again

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()