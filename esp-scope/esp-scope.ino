#include <driver/adc.h>
#include <Arduino.h>

#define SAMPLE_RATE 1000000  // Target sample rate: 1MSPS
#define ADC_CHANNEL ADC1_CHANNEL_0  // GPIO1 (ADC1 Channel 0)
#define BUFFER_SIZE 2048  // Increased buffer size for faster sampling

void setup() {
  Serial.begin(2000000);  // Set a higher baud rate for faster data transfer
  pinMode(1, INPUT);  // Set GPIO1 as input

  adc1_config_width(ADC_WIDTH_BIT_12);  // Set to 12-bit resolution (0-4095)
  adc1_config_channel_atten(ADC_CHANNEL, ADC_ATTEN_DB_11);  // 11 dB attenuation
}

void loop() {
  uint8_t adc_buffer[BUFFER_SIZE];  // Buffer to store 8-bit ADC samples

  for (int i = 0; i < BUFFER_SIZE; i++) {
    uint16_t raw_value = adc1_get_raw(ADC_CHANNEL);  // Read raw ADC data
    adc_buffer[i] = (raw_value >> 4);  // Convert to 8 bits (0-255)
  }

  Serial.write(adc_buffer, sizeof(adc_buffer));  // Send the entire buffer
}