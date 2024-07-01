#include <Arduino.h>
#include <WiFi.h>


#define ADC_PIN     36  // GPIO 36 (ADC1_CH0) or any other available ADC pin on ESP32-S3
#define SAMPLE_RATE 2000000  // Max sample rate is about 2Msps for ESP32 ADC
#define BUFFER_SIZE 1024  // Define buffer size for collecting ADC samples

uint16_t adc_buffer[BUFFER_SIZE];  // Buffer to store ADC readings

void setup() {
  // Initialize Serial communication at 2M baud rate
  Serial.begin(1000000);

  // Initialize ADC
  analogReadResolution(12);  // 12-bit ADC resolution
  analogSetAttenuation(ADC_11db);  // Set attenuation for full voltage range

  // Disable Wi-Fi and Bluetooth to maximize ADC performance
  WiFi.mode(WIFI_OFF);
  btStop();  // Turn off Bluetooth
}

void loop() {
  // Collect ADC samples into the buffer
  for (int i = 0; i < BUFFER_SIZE; i++) {
    adc_buffer[i] = analogRead(ADC_PIN);
  }

  // Send the ADC data over Serial (as binary data)
  Serial.write((uint8_t*)adc_buffer, BUFFER_SIZE * sizeof(uint16_t));
}
