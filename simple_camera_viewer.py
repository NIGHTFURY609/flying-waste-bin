"""
Simple ESP32-CAM Viewer - Display What Camera Sees

This Python script displays whatever the ESP32-CAM sees in a window.
Just shows the live camera feed, nothing else.

Usage:
1. Upload esp32_simple_display.ino to ESP32-CAM
2. Change the IP address below to your ESP32-CAM's IP
3. Run: python simple_camera_viewer.py
"""

import cv2
import time

def main():
    print("ESP32-CAM Simple Viewer")
    print("=" * 25)
    
    # CHANGE THIS to your ESP32-CAM's IP address
    ESP32_IP = "192.168.1.100"  # <-- UPDATE THIS IP ADDRESS
    
    stream_url = f"http://{ESP32_IP}/"
    
    print(f"Connecting to ESP32-CAM at: {stream_url}")
    print("Make sure:")
    print("1. ESP32-CAM is uploaded with esp32_simple_display.ino")
    print("2. ESP32-CAM is connected to WiFi")
    print("3. IP address above is correct")
    print()
    
    # Open video stream
    print("Opening camera stream...")
    cap = cv2.VideoCapture(stream_url)
    
    if not cap.isOpened():
        print("❌ Cannot connect to ESP32-CAM")
        print(f"Make sure ESP32-CAM is accessible at {ESP32_IP}")
        print("Try opening this URL in your browser first:")
        print(f"  {stream_url}")
        return
    
    print("✓ Connected to ESP32-CAM!")
    print("✓ Camera window will open...")
    print("Press 'q' to quit")
    print()
    
    frame_count = 0
    
    try:
        while True:
            # Read frame from ESP32-CAM
            ret, frame = cap.read()
            
            if not ret:
                print("❌ Lost connection to camera")
                break
            
            frame_count += 1
            
            # Add simple frame counter
            cv2.putText(frame, f"Frame: {frame_count}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Display the frame
            cv2.imshow('ESP32-CAM - What Camera Sees', frame)
            
            # Check for quit key
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("User pressed 'q' - closing...")
                break
                
    except KeyboardInterrupt:
        print("\nStopped by user")
    
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print(f"✓ Displayed {frame_count} frames")
        print("✓ Camera viewer closed")

if __name__ == "__main__":
    main()
