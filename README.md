# Flying Waste Bin
An over-engineered waste bin that automatically moves to catch falling objects using computer vision and motion detection.

## System Components

1. **ESP32-CAM** - Captures video and streams it over WiFi
2. **Computer** - Processes video stream for motion detection 
3. **Arduino Uno** - Controls motors to move the waste bin

## Files Structure

- `esp32_cam_stream.ino` - Arduino IDE code for ESP32-CAM module
- `computer_controller.py` - Python script for motion detection and control
- `arduino_motor_controller.ino` - Arduino IDE code for motor control
- `app.py` - Original prototype using local camera
- `requirements.txt` - Python dependencies
- `SETUP_GUIDE.md` - Detailed setup and configuration instructions

## Quick Start

1. Upload `esp32_cam_stream.ino` to ESP32-CAM using Arduino IDE
2. Upload `arduino_motor_controller.ino` to Arduino Uno using Arduino IDE  
3. Install Python dependencies: `pip install -r requirements.txt`
4. Update IP addresses and ports in `computer_controller.py`
5. Run: `python computer_controller.py`

See `SETUP_GUIDE.md` for detailed setup instructions and hardware connections.
