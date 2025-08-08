/*
  ESP32-CAM Direct USB Test with Object Detection
  
  This code allows you to test the ESP32-CAM directly connected to your computer
  via USB/Serial. It captures frames and sends basic object detection data
  over serial communication.
  
  Hardware Setup:
  - Connect ESP32-CAM to computer via FTDI programmer or USB-TTL converter
  - Make sure to connect:
    - VCC -> 5V
    - GND -> GND  
    - U0R (RX) -> TX of FTDI
    - U0T (TX) -> RX of FTDI
    - GPIO 0 -> GND (for programming mode, disconnect after upload)
  
  Serial Output Format:
  - "CAMERA_READY" when camera initializes
  - "OBJECT_DETECTED:X:Y:W:H" when motion is detected
  - "NO_OBJECT" when no motion detected
  - "ERROR:message" for any errors
*/

#include "esp_camera.h"
#include "Arduino.h"

// Camera pin definitions for AI-Thinker ESP32-CAM
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// LED pin for status indication
#define LED_PIN 33  // Built-in LED on ESP32-CAM

// Variables for basic motion detection
camera_fb_t *previous_frame = NULL;
camera_fb_t *current_frame = NULL;
unsigned long last_detection_time = 0;
const unsigned long detection_interval = 500; // Check every 500ms
const int motion_threshold = 30; // Sensitivity threshold
const int min_changed_pixels = 100; // Minimum pixels that must change

void setup() {
  Serial.begin(115200);
  Serial.setDebugOutput(false); // Disable debug to keep serial clean
  
  // Initialize LED
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  
  // Brief startup indication
  for(int i = 0; i < 3; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(200);
    digitalWrite(LED_PIN, LOW);
    delay(200);
  }
  
  Serial.println("ESP32-CAM Direct Test Starting...");
  
  // Camera configuration
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_GRAYSCALE; // Use grayscale for easier processing
  
  // Use smaller frame size for faster processing
  config.frame_size = FRAMESIZE_QVGA; // 320x240
  config.jpeg_quality = 12;
  config.fb_count = 1;
  
  // Initialize camera
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.print("ERROR:Camera init failed with error 0x");
    Serial.println(err, HEX);
    return;
  }
  
  // Get sensor handle for additional settings
  sensor_t * s = esp_camera_sensor_get();
  if (s) {
    // Flip camera if needed
    s->set_vflip(s, 1);        // Vertical flip
    s->set_hmirror(s, 1);      // Horizontal mirror
    
    // Adjust settings for better motion detection
    s->set_brightness(s, 0);   // -2 to 2
    s->set_contrast(s, 0);     // -2 to 2
    s->set_saturation(s, 0);   // -2 to 2
  }
  
  Serial.println("CAMERA_READY");
  digitalWrite(LED_PIN, HIGH); // Solid LED when ready
}

void loop() {
  // Check if it's time for detection
  if (millis() - last_detection_time < detection_interval) {
    delay(10);
    return;
  }
  
  last_detection_time = millis();
  
  // Capture current frame
  current_frame = esp_camera_fb_get();
  if (!current_frame) {
    Serial.println("ERROR:Failed to capture frame");
    return;
  }
  
  // If we have a previous frame, compare for motion
  if (previous_frame != NULL) {
    detectMotion();
  }
  
  // Store current frame as previous for next comparison
  if (previous_frame != NULL) {
    esp_camera_fb_return(previous_frame);
  }
  previous_frame = current_frame;
  current_frame = NULL;
}

void detectMotion() {
  if (!previous_frame || !current_frame) {
    return;
  }
  
  // Make sure both frames are the same size
  if (previous_frame->len != current_frame->len) {
    Serial.println("ERROR:Frame size mismatch");
    return;
  }
  
  int width = current_frame->width;
  int height = current_frame->height;
  int changed_pixels = 0;
  int motion_x = 0, motion_y = 0;
  int motion_count = 0;
  
  // Compare pixels (simple frame differencing)
  for (int y = 0; y < height; y += 4) { // Skip pixels for speed
    for (int x = 0; x < width; x += 4) {
      int index = y * width + x;
      
      if (index < previous_frame->len && index < current_frame->len) {
        int diff = abs(current_frame->buf[index] - previous_frame->buf[index]);
        
        if (diff > motion_threshold) {
          changed_pixels++;
          motion_x += x;
          motion_y += y;
          motion_count++;
        }
      }
    }
  }
  
  // Check if enough pixels changed to indicate motion
  if (changed_pixels > min_changed_pixels && motion_count > 0) {
    // Calculate average position of motion
    int avg_x = motion_x / motion_count;
    int avg_y = motion_y / motion_count;
    
    // Estimate object size (rough approximation)
    int obj_width = sqrt(changed_pixels) * 4; // Rough estimation
    int obj_height = obj_width;
    
    // Blink LED to indicate detection
    digitalWrite(LED_PIN, LOW);
    delay(50);
    digitalWrite(LED_PIN, HIGH);
    
    // Send detection data over serial
    Serial.print("OBJECT_DETECTED:");
    Serial.print(avg_x);
    Serial.print(":");
    Serial.print(avg_y);
    Serial.print(":");
    Serial.print(obj_width);
    Serial.print(":");
    Serial.print(obj_height);
    Serial.print(":");
    Serial.println(changed_pixels); // Include number of changed pixels
    
  } else {
    Serial.println("NO_OBJECT");
  }
}

// Optional: Function to send raw frame data over serial (for debugging)
void sendFrameData() {
  if (!current_frame) return;
  
  Serial.print("FRAME_DATA:");
  Serial.print(current_frame->width);
  Serial.print(":");
  Serial.print(current_frame->height);
  Serial.print(":");
  
  // Send first few bytes of frame data (for verification)
  for(int i = 0; i < 10 && i < current_frame->len; i++) {
    Serial.print(current_frame->buf[i]);
    if(i < 9) Serial.print(",");
  }
  Serial.println();
}
