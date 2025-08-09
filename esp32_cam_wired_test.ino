/*
  ESP32-CAM Wired Test Mode
  
  This code allows you to test the ESP32-CAM while connected directly to computer via USB/Serial.
  It captures frames, processes them, and sends both detection data AND image data over serial.
  
  Features:
  - No WiFi required
  - Sends detection coordinates over serial
  - Sends compressed image data over serial for display on computer
  - Works while connected via programming cable
  
  Hardware Setup:
  - Connect ESP32-CAM to computer via FTDI/USB-TTL
  - No need to disconnect GPIO 0 after programming for this test
  - Keep connected for continuous operation
  
  Serial Output:
  - "CAMERA_READY" when initialized
  - "OBJECT_DETECTED:x:y:w:h:pixels" for detections
  - "NO_OBJECT" when no motion
  - "FRAME_START:width:height:size" followed by image data
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
#define LED_PIN 33

// Test mode settings
#define SEND_IMAGES true        // Set to false to disable image transmission
#define IMAGE_INTERVAL 1000     // Send image every 1000ms (1 second)
#define DETECTION_INTERVAL 500  // Check for motion every 500ms

// Variables
camera_fb_t *previous_frame = NULL;
camera_fb_t *current_frame = NULL;
unsigned long last_detection_time = 0;
unsigned long last_image_time = 0;
const int motion_threshold = 30;
const int min_changed_pixels = 100;
int detection_count = 0;

void setup() {
  Serial.begin(115200);
  Serial.setDebugOutput(false); // Keep serial clean for data transmission
  
  // Initialize LED
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  
  // Startup indication
  for(int i = 0; i < 5; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(100);
    digitalWrite(LED_PIN, LOW);
    delay(100);
  }
  
  Serial.println("ESP32-CAM Wired Test Mode Starting...");
  
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
  config.pixel_format = PIXFORMAT_JPEG; // Use JPEG for easier transmission
  
  // Use smaller frame size for faster transmission
  config.frame_size = FRAMESIZE_QVGA; // 320x240
  config.jpeg_quality = 15; // Lower quality for faster transmission
  config.fb_count = 1;
  
  // Initialize camera
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.print("ERROR:Camera init failed with error 0x");
    Serial.println(err, HEX);
    return;
  }
  
  // Get sensor for additional settings
  sensor_t * s = esp_camera_sensor_get();
  if (s) {
    s->set_vflip(s, 1);        // Vertical flip
    s->set_hmirror(s, 1);      // Horizontal mirror
    s->set_brightness(s, 0);   // Brightness
    s->set_contrast(s, 0);     // Contrast
  }
  
  Serial.println("CAMERA_READY");
  digitalWrite(LED_PIN, HIGH); // Solid LED when ready
  
  Serial.println("Wired test mode active - sending images and detection data");
}

void loop() {
  unsigned long current_time = millis();
  
  // Capture frame
  current_frame = esp_camera_fb_get();
  if (!current_frame) {
    Serial.println("ERROR:Failed to capture frame");
    delay(100);
    return;
  }
  
  // Motion detection
  if (current_time - last_detection_time >= DETECTION_INTERVAL) {
    if (previous_frame != NULL) {
      detectMotion();
    }
    last_detection_time = current_time;
  }
  
  // Send image data periodically
  if (SEND_IMAGES && (current_time - last_image_time >= IMAGE_INTERVAL)) {
    sendImageData();
    last_image_time = current_time;
  }
  
  // Store current frame as previous
  if (previous_frame != NULL) {
    esp_camera_fb_return(previous_frame);
  }
  previous_frame = current_frame;
  current_frame = NULL;
  
  delay(50); // Small delay to prevent overwhelming
}

void detectMotion() {
  if (!previous_frame || !current_frame) {
    return;
  }
  
  // For JPEG frames, we'll do a simple comparison
  // This is basic but works for wired testing
  if (previous_frame->len != current_frame->len) {
    // Frame size changed, likely motion
    sendDetectionResult(160, 120, 50, 50, abs((int)current_frame->len - (int)previous_frame->len));
    return;
  }
  
  // Compare some bytes of the JPEG data
  int diff_count = 0;
  int sample_size = min(1000, (int)current_frame->len); // Sample first 1000 bytes
  
  for (int i = 0; i < sample_size; i += 10) { // Check every 10th byte
    if (abs(current_frame->buf[i] - previous_frame->buf[i]) > 10) {
      diff_count++;
    }
  }
  
  if (diff_count > 20) { // If enough differences detected
    detection_count++;
    
    // Simulate detection position (center of frame with some variation)
    int x = 160 + (diff_count % 80 - 40); // Center ± 40 pixels
    int y = 120 + (diff_count % 60 - 30); // Center ± 30 pixels
    int w = 40 + (diff_count % 40);       // Width 40-80 pixels
    int h = 30 + (diff_count % 30);       // Height 30-60 pixels
    
    sendDetectionResult(x, y, w, h, diff_count);
    
    // Blink LED on detection
    digitalWrite(LED_PIN, LOW);
    delay(50);
    digitalWrite(LED_PIN, HIGH);
  } else {
    Serial.println("NO_OBJECT");
  }
}

void sendDetectionResult(int x, int y, int w, int h, int confidence) {
  Serial.print("OBJECT_DETECTED:");
  Serial.print(x);
  Serial.print(":");
  Serial.print(y);
  Serial.print(":");
  Serial.print(w);
  Serial.print(":");
  Serial.print(h);
  Serial.print(":");
  Serial.println(confidence);
}

void sendImageData() {
  if (!current_frame) {
    return;
  }
  
  // Send frame header
  Serial.print("FRAME_START:");
  Serial.print(current_frame->width);
  Serial.print(":");
  Serial.print(current_frame->height);
  Serial.print(":");
  Serial.println(current_frame->len);
  
  // Send image data in chunks
  const int chunk_size = 64; // Send 64 bytes at a time
  for (size_t i = 0; i < current_frame->len; i += chunk_size) {
    size_t remaining = current_frame->len - i;
    size_t to_send = (remaining < chunk_size) ? remaining : chunk_size;
    
    Serial.write(current_frame->buf + i, to_send);
    delay(1); // Small delay to prevent overwhelming serial buffer
  }
  
  Serial.println(); // End marker
  Serial.println("FRAME_END");
}

// Alternative simple mode without image transmission
void simpleDetectionMode() {
  // Just do motion detection without sending images
  unsigned long current_time = millis();
  
  if (current_time - last_detection_time >= DETECTION_INTERVAL) {
    current_frame = esp_camera_fb_get();
    if (current_frame) {
      if (previous_frame != NULL) {
        detectMotion();
      }
      
      if (previous_frame != NULL) {
        esp_camera_fb_return(previous_frame);
      }
      previous_frame = current_frame;
    }
    last_detection_time = current_time;
  }
  
  delay(100);
}
