import cv2
import numpy as np
import serial
import time
import requests
from urllib.parse import urlparse

class MotionDetectionController:
    def __init__(self, esp32_ip="192.168.1.100", arduino_port="COM3", arduino_baud=9600):
        """
        Initialize the motion detection controller
        
        Args:
            esp32_ip: IP address of the ESP32-CAM
            arduino_port: Serial port for Arduino Uno (e.g., "COM3" on Windows, "/dev/ttyUSB0" on Linux)
            arduino_baud: Baud rate for Arduino communication
        """
        self.esp32_stream_url = f"http://{esp32_ip}/stream"
        self.arduino_port = arduino_port
        self.arduino_baud = arduino_baud
        self.arduino = None
        
        # Motion detection parameters
        self.backSub = cv2.createBackgroundSubtractorMOG2(history=100, varThreshold=50, detectShadows=True)
        self.kernel = np.ones((5, 5), np.uint8)
        self.min_contour_area = 500
        
        # Initialize serial connection to Arduino
        self.init_arduino_connection()
        
    def init_arduino_connection(self):
        """Initialize serial connection to Arduino Uno"""
        try:
            self.arduino = serial.Serial(self.arduino_port, self.arduino_baud, timeout=1)
            time.sleep(2)  # Give Arduino time to initialize
            print(f"Arduino connected on {self.arduino_port}")
        except serial.SerialException as e:
            print(f"Error connecting to Arduino: {e}")
            print("Make sure Arduino is connected and the port is correct")
            
    def send_command_to_arduino(self, command):
        """
        Send movement command to Arduino
        
        Args:
            command: String command ("Move Left", "Move Right", "Stay")
        """
        if self.arduino and self.arduino.is_open:
            try:
                # Map commands to simple characters for Arduino
                command_map = {
                    "Move Left": "L",
                    "Move Right": "R", 
                    "Stay": "S"
                }
                
                if command in command_map:
                    self.arduino.write(command_map[command].encode())
                    print(f"Sent to Arduino: {command} ({command_map[command]})")
                    
            except serial.SerialException as e:
                print(f"Error sending command to Arduino: {e}")
        else:
            print(f"Arduino not connected. Command: {command}")
            
    def process_frame(self, frame):
        """
        Process a single frame for motion detection
        
        Args:
            frame: OpenCV frame from camera
            
        Returns:
            tuple: (processed_frame, command)
        """
        # Flip frame to correct mirror effect
        frame = cv2.flip(frame, 1)
        
        # Apply background subtraction
        fg_mask = self.backSub.apply(frame)
        
        # Clean up the mask
        fg_mask = cv2.erode(fg_mask, self.kernel, iterations=1)
        fg_mask = cv2.dilate(fg_mask, self.kernel, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        command = "Stay"
        
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            
            if cv2.contourArea(largest_contour) > self.min_contour_area:
                # Get bounding box and center
                x, y, w, h = cv2.boundingRect(largest_contour)
                center_x = x + w // 2
                
                # Draw rectangle around detected object
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
                # Determine movement command
                frame_width = frame.shape[1]
                zone_width = frame_width / 3
                
                if center_x < zone_width:
                    command = "Move Left"
                elif center_x > zone_width * 2:
                    command = "Move Right"
                else:
                    command = "Stay"
                    
                # Draw zone lines for visualization
                cv2.line(frame, (int(zone_width), 0), (int(zone_width), frame.shape[0]), (255, 0, 0), 2)
                cv2.line(frame, (int(zone_width * 2), 0), (int(zone_width * 2), frame.shape[0]), (255, 0, 0), 2)
                
                # Draw center point
                cv2.circle(frame, (center_x, y + h//2), 5, (0, 0, 255), -1)
        
        # Display command on frame
        cv2.putText(frame, command, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
        
        return frame, command
        
    def run_with_esp32_stream(self):
        """Run motion detection using ESP32-CAM stream"""
        print(f"Connecting to ESP32-CAM stream: {self.esp32_stream_url}")
        
        # Open video stream from ESP32-CAM
        cap = cv2.VideoCapture(self.esp32_stream_url)
        
        if not cap.isOpened():
            print("Error: Could not connect to ESP32-CAM stream")
            print("Make sure ESP32-CAM is connected and streaming")
            return
            
        print("Connected to ESP32-CAM stream successfully!")
        print("Press 'q' to quit")
        
        last_command = ""
        command_delay = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Could not read frame from stream")
                break
                
            # Process frame for motion detection
            processed_frame, command = self.process_frame(frame)
            
            # Send command to Arduino (with delay to avoid spam)
            if command != last_command or command_delay <= 0:
                self.send_command_to_arduino(command)
                last_command = command
                command_delay = 10  # Send command every 10 frames if different
            else:
                command_delay -= 1
            
            # Display frame
            cv2.imshow('ESP32-CAM Motion Detection', processed_frame)
            
            # Check for quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        cap.release()
        cv2.destroyAllWindows()
        
    def run_with_local_camera(self):
        """Run motion detection using local computer camera (for testing)"""
        print("Using local camera for testing...")
        
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("Error: Could not open local camera")
            return
            
        print("Local camera opened successfully!")
        print("Press 'q' to quit")
        
        last_command = ""
        command_delay = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Process frame for motion detection
            processed_frame, command = self.process_frame(frame)
            
            # Send command to Arduino (with delay to avoid spam)
            if command != last_command or command_delay <= 0:
                self.send_command_to_arduino(command)
                last_command = command
                command_delay = 10
            else:
                command_delay -= 1
            
            # Display frame
            cv2.imshow('Local Camera Motion Detection', processed_frame)
            
            # Check for quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        cap.release()
        cv2.destroyAllWindows()
        
    def cleanup(self):
        """Clean up resources"""
        if self.arduino and self.arduino.is_open:
            self.arduino.close()
            print("Arduino connection closed")

def main():
    # Configuration - Update these values for your setup
    ESP32_IP = "192.168.1.100"  # Replace with your ESP32-CAM IP address
    ARDUINO_PORT = "COM3"       # Replace with your Arduino port (Windows: COM3, Linux: /dev/ttyUSB0)
    ARDUINO_BAUD = 9600
    
    # Create controller instance
    controller = MotionDetectionController(ESP32_IP, ARDUINO_PORT, ARDUINO_BAUD)
    
    try:
        # Choose which camera to use
        print("Motion Detection Controller")
        print("1. Use ESP32-CAM stream")
        print("2. Use local camera (for testing)")
        choice = input("Enter choice (1 or 2): ").strip()
        
        if choice == "1":
            controller.run_with_esp32_stream()
        elif choice == "2":
            controller.run_with_local_camera()
        else:
            print("Invalid choice")
            
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        controller.cleanup()

if __name__ == "__main__":
    main()
