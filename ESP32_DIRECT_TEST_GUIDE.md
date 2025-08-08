# ESP32-CAM Direct USB Testing Guide

This guide helps you test the ESP32-CAM object detection directly connected to your computer via USB, without needing WiFi.

## Files for Direct Testing

1. **`esp32_cam_direct_test.ino`** - Arduino code for ESP32-CAM
2. **`test_esp32_simple.py`** - Simple console-based Python tester
3. **`test_esp32_direct.py`** - Advanced Python tester with visual plots

## Hardware Setup

### Required Components:
- ESP32-CAM module
- FTDI programmer or USB-to-TTL converter
- Jumper wires
- Computer with USB port

### Wiring Connections:

```
FTDI/USB-TTL    ->  ESP32-CAM
VCC (5V)        ->  5V
GND             ->  GND
TX              ->  U0R (RX)
RX              ->  U0T (TX)
```

**For Programming Mode Only:**
```
GPIO 0          ->  GND (connect only during upload, disconnect after)
```

## Software Setup

### 1. Arduino IDE Setup

1. **Install ESP32 board support** (if not done already):
   - File > Preferences
   - Add URL: `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
   - Tools > Board > Board Manager > Search "ESP32" > Install

2. **Upload the test code**:
   - Open `esp32_cam_direct_test.ino` in Arduino IDE
   - Select Board: "AI Thinker ESP32-CAM"
   - Select Port: Your FTDI programmer port (COM3, COM4, etc.)
   - **Important**: Connect GPIO 0 to GND before uploading
   - Click Upload
   - **Important**: Disconnect GPIO 0 from GND after upload
   - Press the reset button on ESP32-CAM

### 2. Python Environment

Install dependencies:
```bash
pip install pyserial matplotlib
```

## Running the Tests

### Option 1: Simple Console Test (Recommended for first test)

```bash
python test_esp32_simple.py
```

**What it does:**
- Shows camera initialization status
- Displays object detection results in console
- Shows movement commands (Left/Right/Stay)
- No graphics, just text output

### Option 2: Advanced Visual Test

```bash
python test_esp32_direct.py
```

**What it does:**
- Real-time visualization of object positions
- Plots detection activity over time
- Shows detection zones
- Requires matplotlib

## Understanding the Output

### Serial Messages from ESP32-CAM:

- `CAMERA_READY` - Camera initialized successfully
- `OBJECT_DETECTED:X:Y:W:H:pixels` - Object found at position (X,Y) with size W×H
- `NO_OBJECT` - No motion detected
- `ERROR:message` - Something went wrong

### Detection Zones:

The 320×240 camera view is divided into 3 zones:
- **Left Zone** (0-106): "Move Left" command
- **Center Zone** (107-213): "Stay" command  
- **Right Zone** (214-320): "Move Right" command

## Troubleshooting

### ESP32-CAM Issues:

**Upload fails:**
- Make sure GPIO 0 is connected to GND during upload
- Check FTDI connections
- Try different upload speed (115200 → 921600)

**Camera init failed:**
- Check power supply (needs stable 5V)
- Try different ESP32-CAM board (some are defective)
- Check camera ribbon cable connection

**Brown-out detector:**
- Use external 5V power supply instead of FTDI power
- Add capacitor (100µF) between VCC and GND

### Python Issues:

**Serial port not found:**
- Check Device Manager (Windows) for COM port
- Try different COM ports (COM1, COM3, COM4)
- Install FTDI drivers if using FTDI programmer

**Permission denied (Linux):**
```bash
sudo chmod 666 /dev/ttyUSB0
# or add user to dialout group:
sudo usermod -a -G dialout $USER
```

**No object detection:**
- Move objects slowly in front of camera
- Ensure good lighting
- Objects need to be moving to be detected
- Adjust `motion_threshold` in Arduino code if needed

## Testing Procedure

1. **Hardware Check:**
   - Verify all connections
   - Power on ESP32-CAM
   - Check for LED activity

2. **Software Check:**
   - Run simple console test first
   - Verify "CAMERA_READY" message
   - Test object detection with slow movements

3. **Motion Testing:**
   - Move hand slowly in front of camera
   - Try different distances (30cm-100cm works best)
   - Test left, center, and right zones
   - Verify correct movement commands

4. **Performance Check:**
   - Note detection frequency
   - Check for false positives
   - Test in different lighting conditions

## Expected Results

### Successful Test Output:
```
[   0.0s] ✓ Camera initialized and ready!
[   0.0s] Move objects in front of camera to test detection...
[   5.2s] 🎯 OBJECT #1
           Position: (85, 120) in LEFT zone
           Size: 24x24, Changed pixels: 156
           Command: Move Left

[   7.8s] 🎯 OBJECT #2
           Position: (180, 110) in CENTER zone
           Size: 32x32, Changed pixels: 203
           Command: Stay
```

### Next Steps:
Once direct testing works, you can:
1. Use the WiFi streaming version (`esp32_cam_stream.ino`)
2. Connect to the full system with Arduino motor control
3. Integrate with the waste bin mechanical system

## Performance Notes

- **Frame Rate**: ~2 FPS (limited by serial communication)
- **Detection Delay**: ~500ms per check
- **Range**: Works best at 30-100cm distance
- **Lighting**: Needs adequate ambient light
- **Movement**: Requires actual motion to detect (not just presence)
