import numpy as np
import matplotlib.pyplot as plt

def find_zero_crossings(data):
    zero_crossings = np.where(np.diff(np.sign(data)))[0]
    return zero_crossings

def extract_one_period(data, zero_crossings):
    if len(zero_crossings) < 2:
        raise ValueError("Not enough zero crossings found to determine one period.")
    start_idx = zero_crossings[0]
    end_idx = zero_crossings[1]
    return data[start_idx:end_idx]

def process_adc_data(data):
    zero_crossings = find_zero_crossings(data)
    one_period_data = extract_one_period(data, zero_crossings)
    return one_period_data

# Simulate a 100 kHz sine wave
signal_frequency = 100e3  # 100 kHz
sampling_rate = 50e3  # 50 kSPS (undersampling)

# Time vector for 50000 samples at 50kSPS
time = np.arange(0, 50000) / sampling_rate

# Generate the sine wave (the signal to be undersampled)
adc_samples = np.sin(2 * np.pi * signal_frequency * time)

# Process the ADC data to extract one period
one_period = process_adc_data(adc_samples)

# Plot the original undersampled sine wave and the extracted one-period wave
plt.figure(figsize=(12, 6))

# Plot the original sine wave (undersampled)
plt.subplot(2, 1, 1)
plt.plot(time, adc_samples, label='Original Sine Wave (Undersampled)', color='blue')
plt.title('Original Sine Wave (Undersampled)')
plt.xlabel('Time [s]')
plt.ylabel('Amplitude')
plt.grid(True)

# Plot the extracted one-period wave
plt.subplot(2, 1, 2)
# Create a new time axis for the extracted one-period data
one_period_time = np.arange(len(one_period)) / sampling_rate
plt.plot(one_period_time, one_period, label='Extracted One Period', color='orange')
plt.title('Recreated Wave from ADC Data (One Period)')
plt.xlabel('Time [s]')
plt.ylabel('Amplitude')
plt.grid(True)

plt.tight_layout()
plt.show()
