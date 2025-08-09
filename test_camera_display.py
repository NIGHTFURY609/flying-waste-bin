"""
Test Local Camera - Make Sure Display Works

This tests your local computer camera to make sure OpenCV display is working.
If this doesn't show a window, there's an OpenCV problem.
"""

import cv2
import time

def test_local_camera():
    print("Testing Local Camera Display")
    print("=" * 30)
    print("This will test your computer's camera to make sure display works")
    print("Press 'q' to quit")
    print()
    
    # Open local camera
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Cannot open local camera")
        print("This might be normal if you don't have a webcam")
        return False
    
    print("✓ Local camera opened")
    print("✓ Camera window should appear...")
    
    frame_count = 0
    
    try:
        while True:
            ret, frame = cap.read()
            
            if not ret:
                print("❌ Cannot read from camera")
                break
            
            frame_count += 1
            
            # Add text overlay
            cv2.putText(frame, "Local Camera Test", (50, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, f"Frame: {frame_count}", (50, 100), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, "Press 'q' to quit", (50, 150), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Show frame
            cv2.imshow('Local Camera Test - If you see this, display works!', frame)
            
            # Check for quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        print("\nStopped by user")
    
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print(f"✓ Displayed {frame_count} frames from local camera")
        return True

def test_fake_camera():
    print("\nTesting Fake Camera (No Hardware Needed)")
    print("=" * 40)
    print("Creating a fake camera feed to test OpenCV display")
    print("Press 'q' to quit")
    print()
    
    import numpy as np
    
    frame_count = 0
    
    try:
        while True:
            # Create a fake frame
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            
            # Add moving elements
            frame_count += 1
            color = (frame_count % 255, (frame_count * 2) % 255, (frame_count * 3) % 255)
            
            # Moving rectangle
            x = (frame_count * 5) % 600
            cv2.rectangle(frame, (x, 200), (x + 40, 280), color, -1)
            
            # Text
            cv2.putText(frame, "FAKE CAMERA TEST", (200, 100), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(frame, f"Frame: {frame_count}", (200, 150), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(frame, "If you see this moving, OpenCV works!", (150, 350), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, "Press 'q' to quit", (200, 400), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Show frame
            cv2.imshow('Fake Camera Test - Testing OpenCV Display', frame)
            
            # Check for quit
            if cv2.waitKey(30) & 0xFF == ord('q'):  # 30ms delay for animation
                break
                
    except KeyboardInterrupt:
        print("\nStopped by user")
    
    finally:
        cv2.destroyAllWindows()
        print(f"✓ Displayed {frame_count} fake frames")
        return True

def main():
    print("CAMERA DISPLAY TEST")
    print("=" * 20)
    print()
    print("This will test if OpenCV can display camera windows on your computer")
    print()
    
    # Test 1: Fake camera (always works if OpenCV is installed)
    print("TEST 1: Fake Camera (No hardware needed)")
    fake_ok = test_fake_camera()
    
    if not fake_ok:
        print("❌ OpenCV display is not working!")
        print("Try: pip install opencv-python --force-reinstall")
        return
    
    print("\n" + "="*50)
    
    # Test 2: Real local camera
    print("TEST 2: Local Camera (if available)")
    local_ok = test_local_camera()
    
    print("\n" + "="*50)
    print("RESULTS:")
    
    if fake_ok:
        print("✅ OpenCV display is working!")
        print("You can now use the ESP32-CAM viewer:")
        print("  python simple_camera_viewer.py")
    
    if local_ok:
        print("✅ Local camera also works!")
    else:
        print("⚠ Local camera not available (this is OK)")
    
    print("\nNext steps:")
    print("1. Upload esp32_simple_display.ino to ESP32-CAM")
    print("2. Update IP address in simple_camera_viewer.py")
    print("3. Run: python simple_camera_viewer.py")

if __name__ == "__main__":
    main()
