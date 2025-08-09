"""
Basic OpenCV Display Test

This is a simple test to verify that OpenCV can display windows on your system.
Run this first to make sure OpenCV is working properly.

If this doesn't show a window, there might be an OpenCV installation issue.
"""

import cv2
import numpy as np
import time

def test_opencv_display():
    """Test basic OpenCV window display"""
    print("Testing OpenCV display functionality...")
    
    # Create a test image
    test_image = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Add some visual elements
    cv2.rectangle(test_image, (50, 50), (590, 430), (100, 100, 100), -1)
    cv2.rectangle(test_image, (50, 50), (590, 430), (255, 255, 255), 3)
    
    # Add text
    cv2.putText(test_image, "OpenCV Display Test", (150, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
    cv2.putText(test_image, "If you see this window, OpenCV is working!", (80, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.putText(test_image, "Press 'q' to close or wait 10 seconds", (120, 350), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
    
    # Add some detection zone lines like ESP32-CAM test
    zone_width = 640 // 3
    cv2.line(test_image, (zone_width, 0), (zone_width, 480), (255, 0, 0), 3)
    cv2.line(test_image, (zone_width * 2, 0), (zone_width * 2, 480), (255, 0, 0), 3)
    
    cv2.putText(test_image, "LEFT", (zone_width//2 - 40, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
    cv2.putText(test_image, "CENTER", (zone_width + 50, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
    cv2.putText(test_image, "RIGHT", (zone_width * 2 + 40, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
    
    print("✓ Test image created")
    print("✓ Opening display window...")
    
    # Try to display the window
    try:
        window_name = 'OpenCV Display Test'
        cv2.imshow(window_name, test_image)
        print("✓ Window should be visible now!")
        print("  If you don't see a window, there might be an OpenCV issue")
        
        # Wait for key press or timeout
        start_time = time.time()
        while time.time() - start_time < 10:  # 10 second timeout
            key = cv2.waitKey(100) & 0xFF
            if key == ord('q'):
                print("✓ User pressed 'q' - test successful!")
                break
        else:
            print("✓ 10 seconds elapsed - test completed!")
            
        cv2.destroyAllWindows()
        print("✓ Window closed successfully")
        return True
        
    except Exception as e:
        print(f"❌ OpenCV display error: {e}")
        return False

def test_webcam():
    """Test webcam access"""
    print("\nTesting webcam access...")
    
    try:
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            print("✓ Webcam opened successfully")
            
            # Try to read a frame
            ret, frame = cap.read()
            if ret:
                print("✓ Frame captured successfully")
                print(f"  Frame size: {frame.shape}")
                
                # Show the frame
                cv2.imshow('Webcam Test - Press q to close', frame)
                print("✓ Displaying webcam frame (press 'q' to close)")
                
                cv2.waitKey(3000)  # Show for 3 seconds
                cv2.destroyAllWindows()
                
            else:
                print("❌ Could not capture frame from webcam")
                
            cap.release()
            return True
        else:
            print("❌ Could not open webcam")
            return False
            
    except Exception as e:
        print(f"❌ Webcam test error: {e}")
        return False

def main():
    print("="*50)
    print("OPENCV AND CAMERA SYSTEM TEST")
    print("="*50)
    print()
    
    print("This test will help diagnose display issues:")
    print("1. Test basic OpenCV window display")
    print("2. Test webcam access and display")
    print()
    
    # Test 1: Basic OpenCV display
    print("TEST 1: Basic OpenCV Display")
    print("-" * 30)
    display_ok = test_opencv_display()
    
    if not display_ok:
        print("\n❌ OpenCV display test failed!")
        print("Possible solutions:")
        print("  - Try: pip install opencv-python --force-reinstall")
        print("  - Check if you have multiple Python installations")
        print("  - Try running from command prompt as administrator")
        print("  - Check Windows display scaling settings")
        return
    
    print("\n" + "="*30)
    
    # Test 2: Webcam test
    print("TEST 2: Webcam Access")
    print("-" * 30)
    webcam_ok = test_webcam()
    
    if webcam_ok:
        print("\n✅ ALL TESTS PASSED!")
        print("Your OpenCV and camera system is working correctly.")
        print("You can now run the ESP32-CAM tests:")
        print("  python test_esp32_simple_display.py")
    else:
        print("\n⚠ Webcam test failed, but OpenCV display works")
        print("The ESP32-CAM tests should still work for serial data")

if __name__ == "__main__":
    main()
