"""
Simple ESP32-CAM Direct Test (Console Only)

A simplified version of the ESP32-CAM tester that only uses console output.
This is easier to run and doesn't require matplotlib.

Usage:
1. Upload esp32_cam_direct_test.ino to your ESP32-CAM
2. Connect ESP32-CAM to computer via FTDI/USB-TTL converter  
3. Update COM_PORT below
4. Run this script: python test_esp32_simple.py
"""

import serial
import time

class SimpleESP32CamTester:
    def __init__(self, com_port="COM3", baud_rate=115200):
        self.com_port = com_port
        self.baud_rate = baud_rate
        self.serial_connection = None
        self.detection_count = 0
        self.start_time = time.time()
        
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
            print("Available ports might be: COM1, COM3, COM4 (Windows) or /dev/ttyUSB0 (Linux)")
            return False
            
    def disconnect(self):
        """Disconnect from ESP32-CAM"""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            print("\n✓ Disconnected from ESP32-CAM")
            
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
            
    def run_test(self):
        """Main test loop"""
        if not self.connect():
            return False
            
        print("\n" + "="*50)
        print("ESP32-CAM DIRECT TEST - Console Mode")
        print("="*50)
        print("Waiting for camera to initialize...")
        print("Press Ctrl+C to stop")
        print()
        
        try:
            while True:
                if self.serial_connection.in_waiting:
                    try:
                        line = self.serial_connection.readline().decode('utf-8').strip()
                        if line:
                            self.process_data(line)
                    except UnicodeDecodeError:
                        # Skip lines that can't be decoded
                        pass
                        
                time.sleep(0.01)  # Small delay to prevent high CPU usage
                
        except KeyboardInterrupt:
            runtime = time.time() - self.start_time
            print(f"\n[{runtime:6.1f}s] Test stopped by user")
            print(f"Total detections: {self.detection_count}")
            
        finally:
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
    COM_PORT = "COM3"  # Change this to your ESP32-CAM port
    
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
    tester = SimpleESP32CamTester(COM_PORT)
    success = tester.run_test()
    
    if success:
        print("Test completed successfully!")
    else:
        print("Test failed - check connections and COM port")

if __name__ == "__main__":
    main()
