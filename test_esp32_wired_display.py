"""
ESP32-CAM Wired Test Display

This script works with the ESP32-CAM in wired test mode (connected via USB/Serial).
It receives both detection data and image data over serial and displays them.

Features:
- Receives live images from ESP32-CAM over serial
- Shows detection overlays on actual ESP32-CAM images
- No WiFi required - pure wired connection
- Real-time display of ESP32-CAM feed

Usage:
1. Upload esp32_cam_wired_test.ino to ESP32-CAM
2. Keep ESP32-CAM connected via USB (don't disconnect GPIO 0)
3. Update COM_PORT below
4. Run: python test_esp32_wired_display.py

Note: This works while ESP32-CAM is in programming mode (GPIO 0 connected to GND)
"""

import serial
import time
import cv2
import numpy as np
import threading
import queue
import struct

class ESP32CamWiredTester:
    def __init__(self, com_port="COM5", baud_rate=115200):
        self.com_port = com_port
        self.baud_rate = baud_rate
        self.serial_connection = None
        
        # Detection and image data
        self.current_detection = None
        self.current_frame = None
        self.detection_count = 0
        self.frame_count = 0
        self.start_time = time.time()
        
        # Threading
        self.running = False
        self.data_queue = queue.Queue()
        self.receiving_frame = False
        self.frame_buffer = bytearray()
        self.expected_frame_size = 0
        self.frame_width = 320
        self.frame_height = 240
        
    def connect(self):
        """Connect to ESP32-CAM via serial"""
        try:
            print(f"Connecting to ESP32-CAM on {self.com_port}...")
            self.serial_connection = serial.Serial(
                self.com_port, 
                self.baud_rate, 
                timeout=2
            )
            time.sleep(2)
            print("✓ Wired connection established")
            return True
        except serial.SerialException as e:
            print(f"❌ Connection failed: {e}")
            print("Make sure ESP32-CAM is connected and COM port is correct")
            return False
            
    def disconnect(self):
        """Disconnect from ESP32-CAM"""
        self.running = False
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            print("✓ Disconnected from ESP32-CAM")
        cv2.destroyAllWindows()
        
    def read_serial_data(self):
        """Read data from ESP32-CAM in background thread"""
        buffer = b""
        
        while self.running:
            try:
                if self.serial_connection and self.serial_connection.in_waiting:
                    # Read available data
                    new_data = self.serial_connection.read(self.serial_connection.in_waiting)
                    buffer += new_data
                    
                    # Process complete lines
                    while b'\n' in buffer:
                        line, buffer = buffer.split(b'\n', 1)
                        try:
                            line_str = line.decode('utf-8').strip()
                            if line_str:
                                self.data_queue.put(('TEXT', line_str))
                        except UnicodeDecodeError:
                            # This might be image data
                            if self.receiving_frame and len(line) > 0:
                                self.data_queue.put(('BINARY', line))
                                
            except Exception as e:
                print(f"Serial read error: {e}")
                break
            time.sleep(0.01)
            
    def process_data(self, data_type, data):
        """Process received data from ESP32-CAM"""
        current_time = time.time()
        runtime = current_time - self.start_time
        
        if data_type == 'TEXT':
            if data == "CAMERA_READY":
                print(f"[{runtime:6.1f}s] ✓ ESP32-CAM wired test mode ready!")
                print(f"[{runtime:6.1f}s] Receiving live images via serial...")
                
            elif data.startswith("OBJECT_DETECTED:"):
                try:
                    parts = data.split(":")
                    x = int(parts[1])
                    y = int(parts[2])
                    w = int(parts[3])
                    h = int(parts[4])
                    confidence = int(parts[5])
                    
                    self.detection_count += 1
                    
                    # Determine command
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
                    
                    self.current_detection = {
                        'x': x, 'y': y, 'w': w, 'h': h,
                        'confidence': confidence, 'command': command,
                        'zone': zone, 'time': current_time
                    }
                    
                    print(f"[{runtime:6.1f}s] 🎯 OBJECT #{self.detection_count}")
                    print(f"           Position: ({x}, {y}) in {zone} zone")
                    print(f"           Command: {command}")
                    
                except (IndexError, ValueError) as e:
                    print(f"[{runtime:6.1f}s] ❌ Error parsing detection: {e}")
                    
            elif data.startswith("FRAME_START:"):
                try:
                    parts = data.split(":")
                    self.frame_width = int(parts[1])
                    self.frame_height = int(parts[2])
                    self.expected_frame_size = int(parts[3])
                    
                    self.receiving_frame = True
                    self.frame_buffer = bytearray()
                    
                    print(f"[{runtime:6.1f}s] 📷 Receiving frame: {self.frame_width}x{self.frame_height}, {self.expected_frame_size} bytes")
                    
                except (IndexError, ValueError) as e:
                    print(f"[{runtime:6.1f}s] ❌ Error parsing frame header: {e}")
                    
            elif data == "FRAME_END":
                if self.receiving_frame:
                    self.process_received_frame()
                    self.receiving_frame = False
                    
            elif data == "NO_OBJECT":
                self.current_detection = None
                
            elif data.startswith("ERROR:"):
                error_msg = data[6:]
                print(f"[{runtime:6.1f}s] ❌ ESP32 Error: {error_msg}")
                
        elif data_type == 'BINARY' and self.receiving_frame:
            self.frame_buffer.extend(data)
            
    def process_received_frame(self):
        """Process a complete frame received from ESP32-CAM"""
        if len(self.frame_buffer) < self.expected_frame_size:
            print(f"⚠ Incomplete frame: got {len(self.frame_buffer)}, expected {self.expected_frame_size}")
            return
            
        try:
            # Decode JPEG image
            frame_data = bytes(self.frame_buffer[:self.expected_frame_size])
            frame_array = np.frombuffer(frame_data, dtype=np.uint8)
            frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
            
            if frame is not None:
                self.current_frame = frame
                self.frame_count += 1
                print(f"✓ Frame {self.frame_count} decoded successfully")
            else:
                print("❌ Failed to decode frame")
                
        except Exception as e:
            print(f"❌ Error processing frame: {e}")
            
    def draw_detection_overlay(self, frame):
        """Draw detection zones and current detection on frame"""
        if frame is None:
            return frame
            
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
        
        # Draw current detection if available and recent
        if self.current_detection and (time.time() - self.current_detection['time'] < 3):
            detection = self.current_detection
            
            x = detection['x']
            y = detection['y']
            w = detection['w']
            h = detection['h']
            
            # Draw bounding box
            cv2.rectangle(frame, (x - w//2, y - h//2), (x + w//2, y + h//2), (0, 255, 0), 3)
            
            # Draw center point
            cv2.circle(frame, (x, y), 5, (0, 0, 255), -1)
            
            # Draw detection info
            info_text = f"Object #{self.detection_count} - {detection['zone']}"
            command_text = f"Command: {detection['command']}"
            
            # Background for text
            cv2.rectangle(frame, (10, height - 80), (400, height - 10), (0, 0, 0), -1)
            
            cv2.putText(frame, info_text, (15, height - 55), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(frame, command_text, (15, height - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Status info
        status_text = f"Frames: {self.frame_count} | Detections: {self.detection_count}"
        cv2.putText(frame, status_text, (10, height - 95), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Instructions
        cv2.putText(frame, "ESP32-CAM Wired Test - Press 'q' to quit", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame
        
    def run_test(self):
        """Main test loop"""
        if not self.connect():
            return False
            
        print("\n" + "="*50)
        print("ESP32-CAM WIRED TEST - Live Display")
        print("="*50)
        print("📸 Receiving live camera feed via serial cable")
        print("🔍 Detection data will appear in console and overlay")
        print("Press 'q' in camera window or Ctrl+C to stop")
        print()
        
        self.running = True
        
        # Start serial reading thread
        serial_thread = threading.Thread(target=self.read_serial_data)
        serial_thread.daemon = True
        serial_thread.start()
        
        try:
            while self.running:
                # Process queued data
                while not self.data_queue.empty():
                    try:
                        data_type, data = self.data_queue.get_nowait()
                        self.process_data(data_type, data)
                    except queue.Empty:
                        break
                
                # Display current frame if available
                if self.current_frame is not None:
                    display_frame = self.draw_detection_overlay(self.current_frame.copy())
                    cv2.imshow('ESP32-CAM Wired Test - Live Feed', display_frame)
                    
                    # Check for quit
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        print("\nCamera window closed")
                        break
                else:
                    time.sleep(0.1)  # Wait for frames
                    
        except KeyboardInterrupt:
            runtime = time.time() - self.start_time
            print(f"\n[{runtime:6.1f}s] Test stopped by user")
            
        finally:
            print(f"Final stats: {self.frame_count} frames, {self.detection_count} detections")
            self.disconnect()
            return True

def main():
    print("ESP32-CAM Wired Test Display")
    print("=" * 30)
    
    # Configuration
    COM_PORT = "COM5"  # Update this to your ESP32-CAM port
    
    print(f"Serial Port: {COM_PORT}")
    print()
    print("Requirements:")
    print("1. ESP32-CAM with esp32_cam_wired_test.ino uploaded")
    print("2. ESP32-CAM connected via USB/Serial (keep GPIO 0 to GND)")
    print("3. No WiFi required - pure wired connection")
    print()
    
    # Create and run tester
    tester = ESP32CamWiredTester(COM_PORT)
    success = tester.run_test()
    
    if success:
        print("✓ Wired test completed successfully!")
    else:
        print("❌ Test failed - check connections and COM port")

if __name__ == "__main__":
    main()
