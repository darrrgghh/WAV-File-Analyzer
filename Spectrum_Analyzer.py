import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile

# Loading the wave file here
fs, data = wavfile.read("audio.wav") # put a .wav file you want to analyze in the root of the project and chang the file name here

# Applying FFT
N = len(data)
spectrum = np.fft.fft(data)
freqs = np.fft.fftfreq(N, 1/fs)

# Visualizing the spectrum
plt.plot(freqs[:N//2], np.abs(spectrum[:N//2]))
plt.xlabel("Frequency (Hz)")
plt.ylabel("Amplitude")
plt.title(".wav file spectrum")
plt.show()