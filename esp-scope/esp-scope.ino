#include <driver/adc.h>
#include <driver/uart.h>
#include <soc/adc_channel.h>

#define SAMPLE_RATE 1000000  // Target sample rate: 1MSPS
#define ADC_CHANNEL ADC1_CHANNEL_0  // GPIO1 (ADC1 Channel 0)
#define BUFFER_SIZE 1024  // Size of the buffer to store ADC samples

void setup() {
  Serial.begin(1000000);  // Set baud rate for faster data transfer
  pinMode(1, INPUT);  // Set GPIO1 as input

  // Configure ADC width and attenuation
  adc1_config_width(ADC_WIDTH_BIT_12);  // 12-bit resolution (0-4095)
  adc1_config_channel_atten(ADC_CHANNEL, ADC_ATTEN_DB_11);  // 11 dB attenuation
}

void loop() {
  uint16_t adc_buffer[BUFFER_SIZE];  // Buffer to store ADC samples

  // Read ADC data in a loop as fast as possible
  for (int i = 0; i < BUFFER_SIZE; i++) {
    adc_buffer[i] = adc1_get_raw(ADC_CHANNEL);  // Read raw ADC data from GPIO1
  }

  // Send raw ADC data over Serial (USB) for each sample
  Serial.write((uint8_t*)adc_buffer, sizeof(adc_buffer));

  // You can use delayMicroseconds() here if you need to fine-tune the sample rate
  // For example, delayMicroseconds(1) will adjust sampling to match approx 1MSPS
}
