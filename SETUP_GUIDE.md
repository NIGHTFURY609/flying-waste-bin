# Flying Waste Bin - Setup Guide

## System Overview
This project consists of three main components:
1. **ESP32-CAM**: Captures video and streams it over WiFi
2. **Computer**: Processes video stream for motion detection and sends commands
3. **Arduino Uno**: Receives commands and controls motors to move the waste bin

## Hardware Requirements

### ESP32-CAM Module
- ESP32-CAM board (AI-Thinker model recommended)
- FTDI programmer or USB-to-TTL converter for programming
- MicroSD card (optional, for local storage)

### Arduino Uno Setup
- Arduino Uno board
- L298N Motor Driver Module
- 2x DC Motors (for movement)
- 12V power supply for motors
- Jumper wires
- Breadboard (optional)

### Computer Requirements
- Python 3.7 or higher
- USB cable for Arduino connection
- WiFi connection to same network as ESP32-CAM

## Software Installation

### 1. Arduino IDE Setup

#### For ESP32-CAM:
1. Install Arduino IDE (1.8.19 or newer)
2. Add ESP32 board package:
   - Go to File > Preferences
   - Add this URL to "Additional Board Manager URLs":
     ```
     https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
     ```
   - Go to Tools > Board > Board Manager
   - Search for "ESP32" and install "esp32 by Espressif Systems"

#### Required Libraries for ESP32-CAM:
- ESP32 Camera library (included with ESP32 package)
- WiFi library (included with ESP32 package)

#### For Arduino Uno:
- No additional libraries required (uses built-in libraries)

### 2. Python Environment Setup

#### Install Python Dependencies:
```bash
pip install -r requirements.txt
```

Or install individually:
```bash
pip install opencv-python numpy pyserial requests
```

## Hardware Connections

### ESP32-CAM Connections
- No additional connections needed for basic camera streaming
- Power: 5V to VCC, GND to GND
- For programming: Connect FTDI programmer to ESP32-CAM pins

### Arduino Uno + L298N Motor Driver

#### L298N to Arduino Connections:
```
L298N Pin    ->  Arduino Pin
ENA          ->  Pin 9 (PWM)
IN1          ->  Pin 7
IN2          ->  Pin 6
ENB          ->  Pin 10 (PWM)
IN3          ->  Pin 5
IN4          ->  Pin 4
VCC          ->  5V
GND          ->  GND
```

#### L298N to Motors:
```
Motor A terminals  ->  Left Motor
Motor B terminals  ->  Right Motor
12V Input         ->  External 12V power supply
GND               ->  Common ground with Arduino
```

## Configuration Steps

### 1. ESP32-CAM Setup

1. Open `esp32_cam_stream.ino` in Arduino IDE
2. Update WiFi credentials:
   ```cpp
   const char* ssid = "YOUR_WIFI_SSID";
   const char* password = "YOUR_WIFI_PASSWORD";
   ```
3. Select Board: "AI Thinker ESP32-CAM"
4. Select Port: Your FTDI programmer port
5. Upload the code
6. Open Serial Monitor to see the IP address
7. Test stream by opening `http://ESP32_IP_ADDRESS/stream` in browser

### 2. Arduino Uno Setup

1. Open `arduino_motor_controller.ino` in Arduino IDE
2. Adjust motor speed if needed:
   ```cpp
   const int motorSpeed = 150;  // 0-255
   ```
3. Select Board: "Arduino Uno"
4. Select Port: Your Arduino's COM port
5. Upload the code
6. Open Serial Monitor to verify communication

### 3. Computer Software Setup

1. Update configuration in `computer_controller.py`:
   ```python
   ESP32_IP = "192.168.1.100"  # Replace with your ESP32-CAM IP
   ARDUINO_PORT = "COM3"       # Windows: COM3, Linux: /dev/ttyUSB0
   ```

2. Run the motion detection:
   ```bash
   python computer_controller.py
   ```

## Usage Instructions

### Starting the System:

1. **Power on ESP32-CAM** and wait for WiFi connection
2. **Connect Arduino Uno** to computer via USB
3. **Run Python script** on computer:
   ```bash
   python computer_controller.py
   ```
4. **Choose input source**:

   - Option 1: ESP32-CAM stream (for final setup)
   - Option 2: Local camera (for testing)

### Testing the System:

1. **Test ESP32-CAM stream**: Open browser and go to `http://ESP32_IP/stream`
2. **Test Arduino**: Open Serial Monitor and send 'L', 'R', or 'S' commands
3. **Test full system**: Run Python script and move in front of camera

### Troubleshooting:

#### ESP32-CAM Issues:
- **No WiFi connection**: Check credentials and network
- **Brown-out detector**: Use stable 5V power supply
- **Upload fails**: Ensure GPIO 0 is connected to GND during upload

#### Arduino Issues:
- **Motors don't move**: Check power supply and connections
- **Wrong direction**: Swap motor wires or modify code
- **No serial communication**: Check COM port and drivers

#### Python Issues:
- **OpenCV error**: Install with `pip install opencv-python`
- **Serial error**: Check Arduino port and permissions
- **Stream error**: Verify ESP32-CAM IP and network connection

## System Flow

1. ESP32-CAM captures video and streams over WiFi
2. Computer receives stream and processes for motion detection
3. Computer determines movement command based on object position
4. Computer sends command to Arduino via serial
5. Arduino controls motors to move waste bin
6. Process repeats continuously

## Customization Options

### Motion Detection Parameters:
- Adjust `min_contour_area` for sensitivity
- Modify zone divisions for different trigger areas
- Change background subtraction parameters

### Motor Control:
- Adjust `motorSpeed` for different movement speeds
- Modify `movementDuration` for longer/shorter movements
- Change motor direction logic based on your mechanical setup

### Performance:
- Adjust ESP32-CAM frame rate and quality
- Modify command sending frequency to Arduino
- Add filtering to reduce jittery movements
