import numpy as np
import time

sample_rate = 100000000
frequency = 50000
amplitude = 512
duration = 1


t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
sine_wave = amplitude * (1 + np.sin(2 * np.pi * frequency * t))

# Trigger parameters
TRIGGER_THRESHOLD = 512
PRE_TRIGGER_SAMPLES = 100
POST_TRIGGER_SAMPLES = 400
TRIGGER_SLOPE = "rising"

# Buffer to store the waveform
pre_trigger_buffer = []
post_trigger_buffer = []
triggered = False

# Simulate reading from the ADC (return values from the sine wave)
def read_adc(index):
    return int(sine_wave[index % len(sine_wave)])

index = 0
while True:
    adc_value = read_adc(index)
    index += 1
    
    if not triggered:
        pre_trigger_buffer.append(adc_value)
        if len(pre_trigger_buffer) > PRE_TRIGGER_SAMPLES:
            pre_trigger_buffer.pop(0)
        if TRIGGER_SLOPE == "rising" and adc_value > TRIGGER_THRESHOLD:
            if len(pre_trigger_buffer) > 1 and pre_trigger_buffer[-2] < TRIGGER_THRESHOLD:
                print("Rising edge trigger detected!")
                triggered = True
        elif TRIGGER_SLOPE == "falling" and adc_value < TRIGGER_THRESHOLD:
            if len(pre_trigger_buffer) > 1 and pre_trigger_buffer[-2] > TRIGGER_THRESHOLD:
                print("Falling edge trigger detected!")
                triggered = True
    else:
        post_trigger_buffer.append(adc_value)
        if len(post_trigger_buffer) >= POST_TRIGGER_SAMPLES:
            break

waveform = pre_trigger_buffer + post_trigger_buffer
print("Captured waveform with {} samples".format(len(waveform)))

import matplotlib.pyplot as plt
plt.plot(waveform)
plt.title('Captured Waveform')
plt.xlabel('Sample Number')
plt.ylabel('ADC Value')
plt.show()
