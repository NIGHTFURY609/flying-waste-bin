"""
ESP32-CAM Direct Test Reader

This script communicates with the ESP32-CAM connected directly via USB/Serial
to test object detection functionality without WiFi.

Make sure to:
1. Upload esp32_cam_direct_test.ino to your ESP32-CAM
2. Connect ESP32-CAM to computer via FTDI/USB-TTL converter
3. Update the COM_PORT below to match your ESP32-CAM's port
4. Run this script to see object detection results

Serial Communication Format:
- Receives: "CAMERA_READY" when camera initializes
- Receives: "OBJECT_DETECTED:X:Y:W:H:pixels" when motion detected
- Receives: "NO_OBJECT" when no motion
- Receives: "ERROR:message" for errors
"""

import serial
import time
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation
import threading
import queue

class ESP32CamTester:
    def __init__(self, com_port="COM3", baud_rate=115200):
        """
        Initialize ESP32-CAM tester
        
        Args:
            com_port: Serial port for ESP32-CAM (Windows: COM3, Linux: /dev/ttyUSB0)
            baud_rate: Serial communication speed
        """
        self.com_port = com_port
        self.baud_rate = baud_rate
        self.serial_connection = None
        self.running = False
        self.data_queue = queue.Queue()
        
        # Detection data
        self.last_detection = None
        self.detection_history = []
        self.max_history = 50
        
        # Visualization
        self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(12, 5))
        self.setup_plots()
        
    def connect(self):
        """Connect to ESP32-CAM via serial"""
        try:
            self.serial_connection = serial.Serial(
                self.com_port, 
                self.baud_rate, 
                timeout=1
            )
            time.sleep(2)  # Give ESP32 time to initialize
            print(f"Connected to ESP32-CAM on {self.com_port}")
            return True
        except serial.SerialException as e:
            print(f"Error connecting to ESP32-CAM: {e}")
            print(f"Make sure ESP32-CAM is connected to {self.com_port}")
            return False
            
    def disconnect(self):
        """Disconnect from ESP32-CAM"""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            print("Disconnected from ESP32-CAM")
            
    def read_serial_data(self):
        """Read data from ESP32-CAM in separate thread"""
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
        
        if data == "CAMERA_READY":
            print("✓ ESP32-CAM camera initialized successfully!")
            
        elif data == "NO_OBJECT":
            # print("No object detected")  # Comment this out to reduce spam
            self.last_detection = None
            
        elif data.startswith("OBJECT_DETECTED:"):
            try:
                parts = data.split(":")
                x = int(parts[1])
                y = int(parts[2])
                w = int(parts[3])
                h = int(parts[4])
                pixels = int(parts[5])
                
                self.last_detection = {
                    'x': x, 'y': y, 'w': w, 'h': h, 
                    'pixels': pixels, 'time': current_time
                }
                
                # Add to history
                self.detection_history.append(self.last_detection.copy())
                if len(self.detection_history) > self.max_history:
                    self.detection_history.pop(0)
                
                print(f"🎯 Object detected at ({x}, {y}) size: {w}x{h}, pixels changed: {pixels}")
                
                # Determine movement suggestion (like original code)
                frame_width = 320  # QVGA width
                zone_width = frame_width / 3
                
                if x < zone_width:
                    command = "Move Left"
                elif x > zone_width * 2:
                    command = "Move Right"
                else:
                    command = "Stay"
                    
                print(f"   → Command: {command}")
                
            except (IndexError, ValueError) as e:
                print(f"Error parsing detection data: {e}")
                
        elif data.startswith("ERROR:"):
            error_msg = data[6:]  # Remove "ERROR:" prefix
            print(f"❌ ESP32-CAM Error: {error_msg}")
            
        else:
            print(f"Unknown data: {data}")
            
    def setup_plots(self):
        """Setup matplotlib plots for visualization"""
        # Left plot: Detection visualization
        self.ax1.set_xlim(0, 320)  # QVGA width
        self.ax1.set_ylim(240, 0)  # QVGA height (inverted Y)
        self.ax1.set_title("Object Detection Visualization")
        self.ax1.set_xlabel("X Position")
        self.ax1.set_ylabel("Y Position") 
        self.ax1.grid(True, alpha=0.3)
        
        # Add zone lines
        zone_width = 320 / 3
        self.ax1.axvline(x=zone_width, color='blue', linestyle='--', alpha=0.7, label='Left Zone')
        self.ax1.axvline(x=zone_width * 2, color='blue', linestyle='--', alpha=0.7, label='Right Zone')
        self.ax1.legend()
        
        # Right plot: Detection frequency over time
        self.ax2.set_title("Detection Activity")
        self.ax2.set_xlabel("Time (seconds ago)")
        self.ax2.set_ylabel("Pixels Changed")
        self.ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
    def update_plots(self, frame):
        """Update visualization plots"""
        current_time = time.time()
        
        # Clear plots
        self.ax1.clear()
        self.ax2.clear()
        self.setup_plots()
        
        # Plot current detection
        if self.last_detection and (current_time - self.last_detection['time'] < 2):
            x, y, w, h = self.last_detection['x'], self.last_detection['y'], self.last_detection['w'], self.last_detection['h']
            
            # Draw bounding box
            rect = patches.Rectangle((x - w//2, y - h//2), w, h, 
                                   linewidth=2, edgecolor='red', facecolor='none')
            self.ax1.add_patch(rect)
            
            # Draw center point
            self.ax1.plot(x, y, 'ro', markersize=8)
            
            # Add text
            self.ax1.text(x, y - 20, f'({x}, {y})', ha='center', va='bottom',
                         bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))
        
        # Plot detection history
        if self.detection_history:
            times = []
            pixels = []
            
            for detection in self.detection_history[-20:]:  # Last 20 detections
                time_ago = current_time - detection['time']
                if time_ago <= 30:  # Show last 30 seconds
                    times.append(time_ago)
                    pixels.append(detection['pixels'])
            
            if times:
                self.ax2.scatter(times, pixels, c='green', alpha=0.6)
                self.ax2.set_xlim(30, 0)  # Reverse time axis (most recent on right)
        
        return []
        
    def run_test(self):
        """Main test loop"""
        if not self.connect():
            return
            
        print("Starting ESP32-CAM test...")
        print("Move objects in front of the camera to test detection")
        print("Press Ctrl+C to stop")
        
        self.running = True
        
        # Start serial reading thread
        serial_thread = threading.Thread(target=self.read_serial_data)
        serial_thread.daemon = True
        serial_thread.start()
        
        # Start animation
        ani = FuncAnimation(self.fig, self.update_plots, interval=100, blit=False)
        
        try:
            # Process data in main thread
            while self.running:
                try:
                    # Process queued serial data
                    while not self.data_queue.empty():
                        data = self.data_queue.get_nowait()
                        self.process_data(data)
                    
                    plt.pause(0.01)  # Keep plot responsive
                    
                except queue.Empty:
                    time.sleep(0.01)
                    
        except KeyboardInterrupt:
            print("\nStopping test...")
            
        finally:
            self.running = False
            self.disconnect()
            plt.close()

def main():
    print("ESP32-CAM Direct Test")
    print("====================")
    
    # Configuration - update these for your setup
    COM_PORT = "COM3"  # Windows: COM3, COM4, etc. Linux: /dev/ttyUSB0, /dev/ttyACM0
    BAUD_RATE = 115200
    
    print(f"Connecting to ESP32-CAM on {COM_PORT}")
    print("Make sure you have:")
    print("1. Uploaded esp32_cam_direct_test.ino to ESP32-CAM")
    print("2. Connected ESP32-CAM to computer via USB/FTDI")
    print("3. Selected the correct COM port above")
    print()
    
    # Create and run tester
    tester = ESP32CamTester(COM_PORT, BAUD_RATE)
    
    try:
        tester.run_test()
    except Exception as e:
        print(f"Test failed: {e}")
        
if __name__ == "__main__":
    main()
