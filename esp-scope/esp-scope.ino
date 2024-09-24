#include <driver/adc.h>
#include <Arduino.h>

#define SAMPLE_RATE 1000000 
#define ADC_CHANNEL ADC1_CHANNEL_0 
#define BUFFER_SIZE 2048 

uint8_t adc_buffer[BUFFER_SIZE];
volatile bool buffer_ready = false; 
SemaphoreHandle_t buffer_semaphore;

void sample_adc_task(void *pvParameters) 
{
  while (true) 
  {
    for (int i = 0; i < BUFFER_SIZE; i++) 
    {
      uint16_t raw_value = adc1_get_raw(ADC_CHANNEL);
      adc_buffer[i] = (raw_value >> 4);
    }
    buffer_ready = true;
    xSemaphoreGive(buffer_semaphore);
    vTaskDelay(pdMS_TO_TICKS(1000 * BUFFER_SIZE / SAMPLE_RATE));
  }
}

void send_serial_task(void *pvParameters) 
{
  while (true) 
  {
    if (xSemaphoreTake(buffer_semaphore, portMAX_DELAY) == pdTRUE) 
    {
      Serial.write(adc_buffer, sizeof(adc_buffer));
    }
  }
}

void setup() 
{
  Serial.begin(2000000);
  pinMode(1, INPUT);
  adc1_config_width(ADC_WIDTH_BIT_12)
  adc1_config_channel_atten(ADC_CHANNEL, ADC_ATTEN_DB_11);
  buffer_semaphore = xSemaphoreCreateBinary();
  xTaskCreatePinnedToCore(sample_adc_task, "ADC Sampling", 4096, NULL, 1, NULL, 1);
  xTaskCreatePinnedToCore(send_serial_task, "Serial Sending", 4096, NULL, 1, NULL, 0);
}

void loop() 
{

}
