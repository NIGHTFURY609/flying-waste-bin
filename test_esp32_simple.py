"""
ESP32-CAM Direct Test with Camera Display

This test script shows the ESP32-CAM video feed on your computer screen
while also displaying object detection results in the console.

Features:
- Live camera feed display using OpenCV
- Real-time object detection visualization
- Console output for detailed detection data
- Detection zones overlay

Usage:
1. Upload esp32_cam_direct_test.ino to your ESP32-CAM
2. Connect ESP32-CAM to computer via FTDI/USB-TTL converter  
3. Update COM_PORT below
4. Run this script: python test_esp32_simple.py
5. Press 'q' to quit the camera window
"""

import serial
import time
import cv2
import numpy as np
import threading
import queue

class ESP32CamTesterWithDisplay:
    def __init__(self, com_port="COM5", baud_rate=115200):
        self.com_port = com_port
        self.baud_rate = baud_rate
        self.serial_connection = None
        self.detection_count = 0
        self.start_time = time.time()
        
        # Camera and display variables
        self.cap = None
        self.current_detection = None
        self.frame_width = 640
        self.frame_height = 480
        self.running = False
        self.data_queue = queue.Queue()
        
        # Try to initialize local camera for display
        self.init_camera()
        
    def init_camera(self):
        """Initialize local camera for display"""
        try:
            # Try to open local camera (webcam)
            self.cap = cv2.VideoCapture(0)
            if self.cap.isOpened():
                # Set resolution
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
                print("✓ Local camera initialized for display")
            else:
                print("⚠ No local camera found - running in console-only mode")
                self.cap = None
        except Exception as e:
            print(f"⚠ Camera initialization failed: {e}")
            self.cap = None
        
    def connect(self):
        """Connect to ESP32-CAM via serial"""
        try:
            print(f"Connecting to ESP32-CAM on {self.com_port}...")
            self.serial_connection = serial.Serial(
                self.com_port, 
                self.baud_rate, 
                timeout=1
            )
            time.sleep(2)  # Give ESP32 time to initialize
            print(f"✓ Connected successfully!")
            return True
        except serial.SerialException as e:
            print(f"❌ Connection failed: {e}")
            print(f"Make sure ESP32-CAM is connected to {self.com_port}")
            print("Available ports might be: COM1, COM5, COM4 (Windows) or /dev/ttyUSB0 (Linux)")
            return False
            
    def disconnect(self):
        """Disconnect from ESP32-CAM and cleanup camera"""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            print("\n✓ Disconnected from ESP32-CAM")
        
        if self.cap:
            self.cap.release()
            cv2.destroyAllWindows()
            print("✓ Camera display closed")
            
    def read_serial_data(self):
        """Read data from ESP32-CAM in background thread"""
        while self.running:
            try:
                if self.serial_connection and self.serial_connection.in_waiting:
                    line = self.serial_connection.readline().decode('utf-8').strip()
                    if line:
                        self.data_queue.put(line)
            except Exception as e:
                print(f"Serial read error: {e}")
                break
            time.sleep(0.01)
            
    def process_data(self, data):
        """Process received data from ESP32-CAM"""
        current_time = time.time()
        runtime = current_time - self.start_time
        
        if data == "CAMERA_READY":
            print(f"[{runtime:6.1f}s] ✓ Camera initialized and ready!")
            print(f"[{runtime:6.1f}s] Move objects in front of camera to test detection...")
            
        elif data == "NO_OBJECT":
            # Show periodic "no object" messages every 10 seconds to show it's working
            if int(runtime) % 10 == 0 and int(runtime * 10) % 10 == 0:
                print(f"[{runtime:6.1f}s] - No object detected (system active)")
            
        elif data.startswith("OBJECT_DETECTED:"):
            try:
                parts = data.split(":")
                x = int(parts[1])
                y = int(parts[2])
                w = int(parts[3])
                h = int(parts[4])
                pixels = int(parts[5])
                
                self.detection_count += 1
                
                # Determine movement command (320x240 QVGA frame)
                frame_width = 320
                zone_width = frame_width / 3
                
                if x < zone_width:
                    command = "Move Left"
                    zone = "LEFT"
                elif x > zone_width * 2:
                    command = "Move Right" 
                    zone = "RIGHT"
                else:
                    command = "Stay"
                    zone = "CENTER"
                
                print(f"[{runtime:6.1f}s] 🎯 OBJECT #{self.detection_count}")
                print(f"           Position: ({x}, {y}) in {zone} zone")
                print(f"           Size: {w}x{h}, Changed pixels: {pixels}")
                print(f"           Command: {command}")
                print()
                
            except (IndexError, ValueError) as e:
                print(f"[{runtime:6.1f}s] ❌ Error parsing detection: {e}")
                
        elif data.startswith("ERROR:"):
            error_msg = data[6:]  # Remove "ERROR:" prefix
            print(f"[{runtime:6.1f}s] ❌ ESP32 Error: {error_msg}")
            
        elif data.strip():  # Only print non-empty lines
            print(f"[{runtime:6.1f}s] ? Unknown: {data}")
            
        # Update current detection for display
        if data.startswith("OBJECT_DETECTED:"):
            try:
                parts = data.split(":")
                x = int(parts[1])
                y = int(parts[2])
                w = int(parts[3])
                h = int(parts[4])
                pixels = int(parts[5])
                
                # Determine command
                frame_width = 320
                zone_width = frame_width / 3
                
                if x < zone_width:
                    command = "Move Left"
                elif x > zone_width * 2:
                    command = "Move Right"
                else:
                    command = "Stay"
                
                self.current_detection = {
                    'x': x, 'y': y, 'w': w, 'h': h,
                    'pixels': pixels, 'command': command,
                    'time': time.time()
                }
            except:
                pass
        elif data == "NO_OBJECT":
            self.current_detection = None
                
    def draw_detection_overlay(self, frame):
        """Draw detection zones and current detection on frame"""
        height, width = frame.shape[:2]
        
        # Draw detection zones
        zone_width = width // 3
        
        # Zone lines
        cv2.line(frame, (zone_width, 0), (zone_width, height), (255, 0, 0), 2)
        cv2.line(frame, (zone_width * 2, 0), (zone_width * 2, height), (255, 0, 0), 2)
        
        # Zone labels
        cv2.putText(frame, "LEFT", (zone_width//2 - 30, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
        cv2.putText(frame, "CENTER", (zone_width + zone_width//2 - 40, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
        cv2.putText(frame, "RIGHT", (zone_width * 2 + zone_width//2 - 35, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
        
        # Draw current detection if available
        if self.current_detection:
            detection = self.current_detection
            
            # Scale coordinates from ESP32-CAM (320x240) to display resolution
            scale_x = width / 320
            scale_y = height / 240
            
            x = int(detection['x'] * scale_x)
            y = int(detection['y'] * scale_y)
            w = int(detection['w'] * scale_x)
            h = int(detection['h'] * scale_y)
            
            # Draw bounding box
            cv2.rectangle(frame, (x - w//2, y - h//2), (x + w//2, y + h//2), (0, 255, 0), 3)
            
            # Draw center point
            cv2.circle(frame, (x, y), 5, (0, 0, 255), -1)
            
            # Draw detection info
            info_text = f"Object #{self.detection_count}"
            command_text = detection.get('command', 'Unknown')
            
            cv2.putText(frame, info_text, (10, height - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"Command: {command_text}", (10, height - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Instructions
        cv2.putText(frame, "Press 'q' to quit", (10, height - 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame
        
    def run_test(self):
        """Main test loop with camera display"""
        if not self.connect():
            return False
            
        print("\n" + "="*50)
        print("ESP32-CAM DIRECT TEST - With Camera Display")
        print("="*50)
        print("Waiting for camera to initialize...")
        
        if self.cap:
            print("Camera display will show local webcam with detection overlay")
        else:
            print("Running in console-only mode (no camera display)")
            
        print("Press Ctrl+C to stop, or 'q' in camera window")
        print()
        
        self.running = True
        
        # Start serial reading thread
        serial_thread = threading.Thread(target=self.read_serial_data)
        serial_thread.daemon = True
        serial_thread.start()
        
        try:
            while self.running:
                # Process queued serial data
                while not self.data_queue.empty():
                    try:
                        data = self.data_queue.get_nowait()
                        self.process_data(data)
                    except queue.Empty:
                        break
                
                # Handle camera display
                if self.cap and self.cap.isOpened():
                    ret, frame = self.cap.read()
                    if ret:
                        # Add detection overlay
                        frame = self.draw_detection_overlay(frame)
                        
                        # Show frame
                        cv2.imshow('ESP32-CAM Test - Local Camera View', frame)
                        
                        # Check for quit key
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            print("\nCamera window closed by user")
                            break
                else:
                    time.sleep(0.1)  # If no camera, just wait
                    
        except KeyboardInterrupt:
            runtime = time.time() - self.start_time
            print(f"\n[{runtime:6.1f}s] Test stopped by user")
            print(f"Total detections: {self.detection_count}")
            
        finally:
            self.running = False
            self.disconnect()
            return True

def test_serial_ports():
    """Test which COM ports are available"""
    import serial.tools.list_ports
    
    print("Available serial ports:")
    ports = serial.tools.list_ports.comports()
    
    if not ports:
        print("  No serial ports found!")
        return []
        
    for port, desc, hwid in sorted(ports):
        print(f"  {port}: {desc}")
        
    return [port for port, _, _ in ports]

def main():
    print("ESP32-CAM Direct Test - Simple Console Version")
    print("=" * 50)
    
    # Show available ports
    available_ports = test_serial_ports()
    print()
    
    # Configuration - update this for your setup
    COM_PORT = "COM5"  # Change this to your ESP32-CAM port
    
    if COM_PORT not in available_ports and available_ports:
        print(f"Warning: {COM_PORT} not found in available ports.")
        print(f"You might want to try: {available_ports[0]}")
        print()
        
    print("Setup checklist:")
    print("1. ✓ Upload esp32_cam_direct_test.ino to ESP32-CAM")
    print("2. ✓ Connect ESP32-CAM to computer via FTDI/USB-TTL")
    print("3. ✓ Update COM_PORT in this script if needed")
    print(f"4. ✓ Using port: {COM_PORT}")
    print()
    
    # Create and run tester
    tester = ESP32CamTesterWithDisplay(COM_PORT)
    success = tester.run_test()
    
    if success:
        print("Test completed successfully!")
    else:
        print("Test failed - check connections and COM port")

if __name__ == "__main__":
    main()
