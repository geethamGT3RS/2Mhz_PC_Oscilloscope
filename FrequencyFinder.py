import numpy as np
import matplotlib.pyplot as plt

sample_rate = 10000
t = np.linspace(0, 1, sample_rate, endpoint=False)
frequency = 50000
amplitude = 1.0
sample_buffer = amplitude * np.sin(2 * np.pi * frequency * t)


fft_result = np.fft.fft(sample_buffer)
frequencies = np.fft.fftfreq(len(sample_buffer), 1.0/sample_rate)
peak_frequency = abs(frequencies[np.argmax(np.abs(fft_result))])
print(f"Dominant Frequency: {peak_frequency} Hz")
