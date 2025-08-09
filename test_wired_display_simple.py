"""
ESP32-CAM Wired Display Viewer - Just Show Camera Feed
======================================================

This Python script receives and displays raw camera images from ESP32-CAM
over USB serial connection. No WiFi needed - just pure camera display.

Requirements:
- ESP32-CAM with esp32_cam_wired_display.ino uploaded
- ESP32-CAM connected via FTDI programmer (keep connected)
- Python with opencv-python and pyserial

Usage:
1. Upload esp32_cam_wired_display.ino to ESP32-CAM
2. Keep ESP32-CAM connected via USB
3. Update COM_PORT below if needed
4. Run: python test_wired_display_simple.py
"""

import serial
import cv2
import numpy as np
import time
import threading
import queue

class ESP32CamWiredDisplay:
    def __init__(self, com_port="COM5", baud_rate=115200):
        self.com_port = com_port
        self.baud_rate = baud_rate
        self.serial_connection = None
        
        # Frame data
        self.current_frame = None
        self.frame_count = 0
        self.start_time = time.time()
        
        # Serial data handling
        self.running = False
        self.frame_buffer = bytearray()
        self.receiving_frame = False
        self.expected_frame_size = 0
        self.frame_width = 0
        self.frame_height = 0
        
        # Create initial placeholder
        self.create_placeholder_frame()
        
    def create_placeholder_frame(self):
        """Create a placeholder frame while waiting for camera"""
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        
        # Background
        cv2.rectangle(frame, (0, 0), (320, 240), (30, 30, 50), -1)
        
        # Title
        cv2.putText(frame, "ESP32-CAM Wired Display", (30, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Status
        cv2.putText(frame, "Waiting for camera feed...", (40, 120), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        # Instructions
        cv2.putText(frame, "1. Upload esp32_cam_wired_display.ino", (10, 160), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)
        cv2.putText(frame, "2. Keep ESP32-CAM connected via USB", (10, 180), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)
        cv2.putText(frame, "3. Press 'q' to quit", (10, 200), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)
        
        self.current_frame = frame
        
    def connect(self):
        """Connect to ESP32-CAM via serial"""
        try:
            print(f"Connecting to ESP32-CAM on {self.com_port}...")
            self.serial_connection = serial.Serial(
                self.com_port, 
                self.baud_rate, 
                timeout=1
            )
            time.sleep(2)
            print("✓ Serial connection established")
            
            # Clear any existing data
            self.serial_connection.flushInput()
            return True
            
        except serial.SerialException as e:
            print(f"❌ Connection failed: {e}")
            print("Available COM ports:")
            self.list_available_ports()
            return False
            
    def list_available_ports(self):
        """List available COM ports"""
        try:
            import serial.tools.list_ports
            ports = serial.tools.list_ports.comports()
            for port in ports:
                print(f"  {port.device}: {port.description}")
        except ImportError:
            print("  Install pyserial to see available ports")
            
    def disconnect(self):
        """Disconnect from ESP32-CAM"""
        self.running = False
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            print("✓ Disconnected from ESP32-CAM")
        cv2.destroyAllWindows()
        
    def read_serial_data(self):
        """Read and process serial data in background thread"""
        while self.running:
            try:
                if self.serial_connection and self.serial_connection.in_waiting:
                    line = self.serial_connection.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        self.process_serial_line(line)
            except Exception as e:
                print(f"Serial read error: {e}")
                break
            time.sleep(0.01)
            
    def process_serial_line(self, line):
        """Process a line of serial data"""
        current_time = time.time()
        runtime = current_time - self.start_time
        
        if line == "CAMERA_READY":
            print(f"[{runtime:6.1f}s] ✓ ESP32-CAM camera ready!")
            
        elif line.startswith("FRAME_START:"):
            # Parse frame header: FRAME_START:size:width:height
            try:
                parts = line.split(":")
                self.expected_frame_size = int(parts[1])
                self.frame_width = int(parts[2])
                self.frame_height = int(parts[3])
                
                print(f"[{runtime:6.1f}s] 📷 Starting frame {self.frame_count + 1}: {self.frame_width}x{self.frame_height}, {self.expected_frame_size} bytes")
                
                # Reset frame buffer
                self.frame_buffer = bytearray()
                self.receiving_frame = True
                
            except (IndexError, ValueError) as e:
                print(f"[{runtime:6.1f}s] ❌ Error parsing frame header: {e}")
                
        elif line.startswith("CHUNK:"):
            # Parse chunk header: CHUNK:size
            try:
                chunk_size = int(line.split(":")[1])
                print(f"[{runtime:6.1f}s] 📦 Receiving chunk: {chunk_size} bytes")
                
                # Read the binary chunk data
                if self.serial_connection:
                    chunk_data = self.serial_connection.read(chunk_size)
                    self.frame_buffer.extend(chunk_data)
                    
                    # Read the end-of-chunk newline
                    self.serial_connection.readline()
                    
            except (IndexError, ValueError) as e:
                print(f"[{runtime:6.1f}s] ❌ Error reading chunk: {e}")
                
        elif line == "FRAME_END":
            if self.receiving_frame:
                self.process_complete_frame()
                self.receiving_frame = False
                
        elif line.startswith("ERROR:"):
            error_msg = line[6:]
            print(f"[{runtime:6.1f}s] ❌ ESP32 Error: {error_msg}")
            
    def process_complete_frame(self):
        """Process a complete frame received from ESP32-CAM"""
        try:
            if len(self.frame_buffer) != self.expected_frame_size:
                print(f"❌ Frame size mismatch: expected {self.expected_frame_size}, got {len(self.frame_buffer)}")
                return
                
            # Decode JPEG image
            frame_np = np.frombuffer(self.frame_buffer, dtype=np.uint8)
            frame = cv2.imdecode(frame_np, cv2.IMREAD_COLOR)
            
            if frame is not None:
                self.current_frame = frame
                self.frame_count += 1
                
                current_time = time.time()
                runtime = current_time - self.start_time
                fps = self.frame_count / runtime if runtime > 0 else 0
                
                print(f"[{runtime:6.1f}s] ✅ Frame {self.frame_count} decoded successfully! FPS: {fps:.1f}")
            else:
                print("❌ Failed to decode JPEG frame")
                
        except Exception as e:
            print(f"❌ Error processing frame: {e}")
            
    def update_placeholder_with_stats(self):
        """Update placeholder frame with current stats"""
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        
        # Background
        cv2.rectangle(frame, (0, 0), (320, 240), (30, 30, 50), -1)
        
        # Title
        cv2.putText(frame, "ESP32-CAM Wired Display", (30, 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Stats
        runtime = time.time() - self.start_time
        fps = self.frame_count / runtime if runtime > 0 else 0
        
        cv2.putText(frame, f"Frames received: {self.frame_count}", (20, 80), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.putText(frame, f"Runtime: {runtime:.1f}s", (20, 100), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.putText(frame, f"FPS: {fps:.1f}", (20, 120), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # Status
        if self.receiving_frame:
            status = f"Receiving frame... {len(self.frame_buffer)}/{self.expected_frame_size}"
            cv2.putText(frame, status, (20, 160), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
        else:
            cv2.putText(frame, "Waiting for next frame...", (20, 160), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
        
        # Instructions
        cv2.putText(frame, "Press 'q' to quit", (20, 200), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)
        
        return frame
        
    def run_display(self):
        """Main display loop"""
        print("\n" + "="*60)
        print("ESP32-CAM WIRED DISPLAY - LIVE CAMERA FEED")
        print("="*60)
        print("📸 This will show live camera feed from ESP32-CAM")
        print("🔌 Make sure ESP32-CAM is connected via USB")
        print("Press 'q' in camera window or Ctrl+C to stop")
        print()
        
        # Try to connect
        connected = self.connect()
        if not connected:
            print("⚠ Serial connection failed, showing display test window...")
            print("Fix the connection and restart to see camera feed")
        
        self.running = True
        
        # Start serial reading thread if connected
        if connected:
            serial_thread = threading.Thread(target=self.read_serial_data)
            serial_thread.daemon = True
            serial_thread.start()
        
        print("Opening camera display window...")
        
        try:
            frame_counter = 0
            while self.running:
                frame_counter += 1
                
                # Get current frame to display
                if self.current_frame is not None:
                    display_frame = self.current_frame.copy()
                    
                    # Add frame info overlay
                    if self.frame_count > 0:
                        runtime = time.time() - self.start_time
                        fps = self.frame_count / runtime if runtime > 0 else 0
                        
                        # Add semi-transparent overlay for text
                        overlay = display_frame.copy()
                        cv2.rectangle(overlay, (5, 5), (315, 45), (0, 0, 0), -1)
                        cv2.addWeighted(overlay, 0.7, display_frame, 0.3, 0, display_frame)
                        
                        # Add text
                        cv2.putText(display_frame, f"Live ESP32-CAM Feed - Frame {self.frame_count}", (10, 20), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                        cv2.putText(display_frame, f"FPS: {fps:.1f} | Press 'q' to quit", (10, 35), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                else:
                    # Show placeholder with stats
                    display_frame = self.update_placeholder_with_stats()
                
                # Resize for better visibility
                display_frame = cv2.resize(display_frame, (640, 480))
                
                # Show frame
                cv2.imshow('ESP32-CAM Wired Display - Live Feed', display_frame)
                
                # Check for quit
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("\nCamera window closed")
                    break
                    
                # Update placeholder every 30 frames if not receiving camera data
                if not connected and frame_counter % 30 == 0:
                    self.update_placeholder_with_stats()
                    
        except KeyboardInterrupt:
            runtime = time.time() - self.start_time
            fps = self.frame_count / runtime if runtime > 0 else 0
            print(f"\n[{runtime:6.1f}s] Test stopped by user")
            print(f"Final stats: {self.frame_count} frames, {fps:.1f} FPS average")
            
        finally:
            self.disconnect()
            return True

def main():
    print("ESP32-CAM Wired Display - Live Camera Feed")
    print("=" * 45)
    
    # Configuration
    COM_PORT = "COM5"  # Update this to your ESP32-CAM port
    
    print(f"Serial Port: {COM_PORT}")
    print()
    print("Setup Steps:")
    print("1. ✓ Upload esp32_cam_wired_display.ino to ESP32-CAM")
    print("2. ✓ Keep ESP32-CAM connected via FTDI/USB")
    print("3. ✓ Make sure COM port is correct")
    print("4. ✓ Run this script to see live camera feed")
    print()
    
    # Create and run display
    display = ESP32CamWiredDisplay(COM_PORT)
    success = display.run_display()
    
    if success:
        print("✓ Display session completed!")
    else:
        print("❌ Display session failed")

if __name__ == "__main__":
    main()
