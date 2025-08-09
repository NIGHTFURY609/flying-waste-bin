"""
ESP32-CAM HTTP Stream Test with Live Video Display

This test connects to the ESP32-CAM via both:
1. Serial connection for object detection data
2. HTTP stream for live video display

This gives you the actual ESP32-CAM video feed with detection overlays.

Requirements:
1. ESP32-CAM running WiFi stream code (esp32_cam_stream.ino)
2. ESP32-CAM also connected via USB for serial detection data
3. Both ESP32-CAM and computer on same WiFi network

Usage:
1. Upload esp32_cam_stream.ino to ESP32-CAM (WiFi version)
2. Connect ESP32-CAM to computer via USB for serial
3. Update ESP32_IP and COM_PORT below
4. Run: python test_esp32_stream_display.py
"""

import serial
import time
import cv2
import numpy as np
import threading
import queue
import requests
from urllib.parse import urlparse

class ESP32CamStreamTester:
    def __init__(self, esp32_ip="192.168.1.100", com_port="COM5", baud_rate=115200):
        self.esp32_ip = esp32_ip
        self.stream_url = f"http://{esp32_ip}/stream"
        self.com_port = com_port
        self.baud_rate = baud_rate
        
        # Connections
        self.serial_connection = None
        self.stream_cap = None
        
        # Detection data
        self.current_detection = None
        self.detection_count = 0
        self.start_time = time.time()
        
        # Threading
        self.running = False
        self.data_queue = queue.Queue()
        
    def connect_serial(self):
        """Connect to ESP32-CAM via serial for detection data"""
        try:
            print(f"Connecting to ESP32-CAM serial on {self.com_port}...")
            self.serial_connection = serial.Serial(
                self.com_port, 
                self.baud_rate, 
                timeout=1
            )
            time.sleep(2)
            print("✓ Serial connection established")
            return True
        except serial.SerialException as e:
            print(f"❌ Serial connection failed: {e}")
            return False
            
    def connect_stream(self):
        """Connect to ESP32-CAM HTTP video stream"""
        try:
            print(f"Connecting to ESP32-CAM stream at {self.stream_url}...")
            
            # Test if stream is available
            response = requests.get(f"http://{self.esp32_ip}/", timeout=5)
            print(f"✓ ESP32-CAM web server responding")
            
            # Open video stream
            self.stream_cap = cv2.VideoCapture(self.stream_url)
            if self.stream_cap.isOpened():
                print("✓ Video stream connection established")
                return True
            else:
                print("❌ Could not open video stream")
                return False
                
        except requests.RequestException as e:
            print(f"❌ Stream connection failed: {e}")
            print(f"Make sure ESP32-CAM is on WiFi and accessible at {self.esp32_ip}")
            return False
            
    def disconnect(self):
        """Disconnect all connections"""
        self.running = False
        
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            print("✓ Serial disconnected")
            
        if self.stream_cap:
            self.stream_cap.release()
            print("✓ Stream disconnected")
            
        cv2.destroyAllWindows()
        
    def read_serial_data(self):
        """Read detection data from serial in background thread"""
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
            
    def process_serial_data(self, data):
        """Process detection data from ESP32-CAM"""
        current_time = time.time()
        runtime = current_time - self.start_time
        
        if data == "CAMERA_READY":
            print(f"[{runtime:6.1f}s] ✓ ESP32-CAM detection system ready!")
            
        elif data.startswith("OBJECT_DETECTED:"):
            try:
                parts = data.split(":")
                x = int(parts[1])
                y = int(parts[2])
                w = int(parts[3])
                h = int(parts[4])
                pixels = int(parts[5])
                
                self.detection_count += 1
                
                # Determine command
                frame_width = 320  # ESP32-CAM QVGA width
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
                
                self.current_detection = {
                    'x': x, 'y': y, 'w': w, 'h': h,
                    'pixels': pixels, 'command': command,
                    'zone': zone, 'time': current_time
                }
                
                print(f"[{runtime:6.1f}s] 🎯 OBJECT #{self.detection_count}")
                print(f"           Position: ({x}, {y}) in {zone} zone")
                print(f"           Command: {command}")
                
            except (IndexError, ValueError) as e:
                print(f"[{runtime:6.1f}s] ❌ Error parsing detection: {e}")
                
        elif data == "NO_OBJECT":
            self.current_detection = None
            
        elif data.startswith("ERROR:"):
            error_msg = data[6:]
            print(f"[{runtime:6.1f}s] ❌ ESP32 Error: {error_msg}")
            
    def draw_detection_overlay(self, frame):
        """Draw detection zones and current detection on video frame"""
        if frame is None:
            return frame
            
        height, width = frame.shape[:2]
        
        # Draw detection zones (scale from 320x240 to actual frame size)
        zone_width = width // 3
        
        # Zone lines
        cv2.line(frame, (zone_width, 0), (zone_width, height), (255, 0, 0), 2)
        cv2.line(frame, (zone_width * 2, 0), (zone_width * 2, height), (255, 0, 0), 2)
        
        # Zone labels
        cv2.putText(frame, "LEFT", (zone_width//2 - 30, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
        cv2.putText(frame, "CENTER", (zone_width + zone_width//2 - 40, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
        cv2.putText(frame, "RIGHT", (zone_width * 2 + zone_width//2 - 35, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
        
        # Draw current detection if available and recent
        if self.current_detection and (time.time() - self.current_detection['time'] < 2):
            detection = self.current_detection
            
            # Scale coordinates from ESP32-CAM resolution to stream resolution
            scale_x = width / 320
            scale_y = height / 240
            
            x = int(detection['x'] * scale_x)
            y = int(detection['y'] * scale_y)
            w = int(detection['w'] * scale_x)
            h = int(detection['h'] * scale_y)
            
            # Draw bounding box
            cv2.rectangle(frame, (x - w//2, y - h//2), (x + w//2, y + h//2), (0, 255, 0), 3)
            
            # Draw center point
            cv2.circle(frame, (x, y), 8, (0, 0, 255), -1)
            
            # Draw detection info
            info_text = f"Object #{self.detection_count} - {detection['zone']}"
            command_text = f"Command: {detection['command']}"
            
            # Background rectangles for text
            cv2.rectangle(frame, (10, height - 80), (400, height - 10), (0, 0, 0), -1)
            
            cv2.putText(frame, info_text, (15, height - 55), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(frame, command_text, (15, height - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Status info
        status_text = f"Detections: {self.detection_count}"
        cv2.putText(frame, status_text, (width - 200, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Instructions
        cv2.putText(frame, "Press 'q' to quit", (10, height - 95), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame
        
    def run_test(self):
        """Main test loop"""
        print("ESP32-CAM HTTP Stream Test with Live Video")
        print("=" * 50)
        
        # Connect to both serial and stream
        if not self.connect_serial():
            print("❌ Serial connection required for detection data")
            return False
            
        if not self.connect_stream():
            print("❌ Stream connection required for video display")
            self.disconnect()
            return False
            
        print("\n✓ All connections established!")
        print("📹 Live video stream will show with detection overlays")
        print("🔍 Detection data will appear in console")
        print("Press 'q' in video window or Ctrl+C to stop")
        print()
        
        self.running = True
        
        # Start serial reading thread
        serial_thread = threading.Thread(target=self.read_serial_data)
        serial_thread.daemon = True
        serial_thread.start()
        
        try:
            while self.running:
                # Process serial data
                while not self.data_queue.empty():
                    try:
                        data = self.data_queue.get_nowait()
                        self.process_serial_data(data)
                    except queue.Empty:
                        break
                
                # Read and display video frame
                if self.stream_cap and self.stream_cap.isOpened():
                    ret, frame = self.stream_cap.read()
                    if ret:
                        # Add detection overlay
                        frame = self.draw_detection_overlay(frame)
                        
                        # Show frame
                        cv2.imshow('ESP32-CAM Live Stream with Detection', frame)
                        
                        # Check for quit
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            print("\nVideo window closed")
                            break
                    else:
                        print("❌ Lost video stream connection")
                        break
                else:
                    time.sleep(0.1)
                    
        except KeyboardInterrupt:
            runtime = time.time() - self.start_time
            print(f"\n[{runtime:6.1f}s] Test stopped by user")
            
        finally:
            print(f"Final detection count: {self.detection_count}")
            self.disconnect()
            return True

def main():
    print("ESP32-CAM HTTP Stream Test")
    print("=" * 30)
    
    # Configuration - Update these for your setup
    ESP32_IP = "192.168.1.100"  # Replace with your ESP32-CAM IP address
    COM_PORT = "COM5"           # Replace with your ESP32-CAM serial port
    
    print(f"ESP32-CAM IP: {ESP32_IP}")
    print(f"Serial Port: {COM_PORT}")
    print()
    print("Requirements:")
    print("1. ESP32-CAM running WiFi stream code (esp32_cam_stream.ino)")
    print("2. ESP32-CAM connected via USB for serial detection data")
    print("3. ESP32-CAM and computer on same WiFi network")
    print()
    
    # Create and run tester
    tester = ESP32CamStreamTester(ESP32_IP, COM_PORT)
    success = tester.run_test()
    
    if success:
        print("✓ Test completed successfully!")
    else:
        print("❌ Test failed - check connections and configuration")

if __name__ == "__main__":
    main()
