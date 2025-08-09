/*
ESP32-CAM Wired Display - Just Show Camera Feed
===============================================

This code streams raw camera images over serial USB connection.
No WiFi needed, no motion detection - just pure camera display.

Hardware Setup:
- ESP32-CAM connected via FTDI programmer
- Keep FTDI connected for power and data
- No GPIO 0 connection needed after upload

Upload Instructions:
1. Connect GPIO 0 to GND for programming
2. Upload this code
3. Remove GPIO 0 connection
4. Reset ESP32-CAM
5. Run Python script to see camera feed
*/

#include "esp_camera.h"
#include "esp_timer.h"

// AI-Thinker ESP32-CAM pin definition
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

void setup() {
  Serial.begin(115200);
  Serial.setDebugOutput(false);
  
  delay(1000);
  
  Serial.println("ESP32-CAM Wired Display Starting...");
  Serial.println("====================================");
  
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
  config.pixel_format = PIXFORMAT_JPEG;
  
  // Frame size - smaller for faster serial transmission
  config.frame_size = FRAMESIZE_QVGA;  // 320x240
  config.jpeg_quality = 15;  // Lower quality = smaller files = faster transmission
  config.fb_count = 1;
  
  // Initialize camera
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("ERROR: Camera init failed with error 0x%x\n", err);
    while(1) {
      delay(1000);
      Serial.println("CAMERA_ERROR");
    }
  }
  
  // Get camera sensor
  sensor_t *s = esp_camera_sensor_get();
  if (s != NULL) {
    // Adjust settings for better image quality
    s->set_brightness(s, 0);     // -2 to 2
    s->set_contrast(s, 1);       // -2 to 2
    s->set_saturation(s, 0);     // -2 to 2
    s->set_special_effect(s, 0); // 0 to 6 (0-No Effect, 1-Negative, 2-Grayscale, 3-Red Tint, 4-Green Tint, 5-Blue Tint, 6-Sepia)
    s->set_whitebal(s, 1);       // 0 = disable , 1 = enable
    s->set_awb_gain(s, 1);       // 0 = disable , 1 = enable
    s->set_wb_mode(s, 0);        // 0 to 4 - if awb_gain enabled (0 - Auto, 1 - Sunny, 2 - Cloudy, 3 - Office, 4 - Home)
    s->set_exposure_ctrl(s, 1);  // 0 = disable , 1 = enable
    s->set_aec2(s, 0);           // 0 = disable , 1 = enable
    s->set_ae_level(s, 0);       // -2 to 2
    s->set_aec_value(s, 300);    // 0 to 1200
    s->set_gain_ctrl(s, 1);      // 0 = disable , 1 = enable
    s->set_agc_gain(s, 0);       // 0 to 30
    s->set_gainceiling(s, (gainceiling_t)0);  // 0 to 6
    s->set_bpc(s, 0);            // 0 = disable , 1 = enable
    s->set_wpc(s, 1);            // 0 = disable , 1 = enable
    s->set_raw_gma(s, 1);        // 0 = disable , 1 = enable
    s->set_lenc(s, 1);           // 0 = disable , 1 = enable
    s->set_hmirror(s, 0);        // 0 = disable , 1 = enable
    s->set_vflip(s, 0);          // 0 = disable , 1 = enable
    s->set_dcw(s, 1);            // 0 = disable , 1 = enable
    s->set_colorbar(s, 0);       // 0 = disable , 1 = enable
  }
  
  Serial.println("CAMERA_READY");
  Serial.println("Starting camera stream...");
  Serial.println("Python script should now display camera feed");
  
  delay(1000);
}

void loop() {
  // Capture image
  camera_fb_t *fb = esp_camera_fb_get();
  
  if (!fb) {
    Serial.println("ERROR: Camera capture failed");
    delay(100);
    return;
  }
  
  // Send frame header
  Serial.print("FRAME_START:");
  Serial.print(fb->len);
  Serial.print(":");
  Serial.print(fb->width);
  Serial.print(":");
  Serial.print(fb->height);
  Serial.println();
  
  // Send image data in chunks
  size_t bytes_sent = 0;
  size_t chunk_size = 1024;  // Send 1KB chunks
  
  while (bytes_sent < fb->len) {
    size_t remaining = fb->len - bytes_sent;
    size_t current_chunk = (remaining < chunk_size) ? remaining : chunk_size;
    
    // Send chunk header
    Serial.print("CHUNK:");
    Serial.print(current_chunk);
    Serial.println();
    
    // Send binary data
    Serial.write(fb->buf + bytes_sent, current_chunk);
    Serial.println(); // End chunk marker
    
    bytes_sent += current_chunk;
    
    // Small delay to prevent overwhelming serial buffer
    delay(10);
  }
  
  // Send frame end marker
  Serial.println("FRAME_END");
  
  // Release frame buffer
  esp_camera_fb_return(fb);
  
  // Small delay between frames
  delay(100);  // ~10 FPS
}
