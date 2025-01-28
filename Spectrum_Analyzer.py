import math
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy.signal import spectrogram

# Function to compute DFT manually (for educational purposes)
def dft_manual(signal):
    num_samples = len(signal)
    x_result = [0] * num_samples  # Initialize an empty list for the result
    for k in range(num_samples):  # Loop through each frequency component
        real = 0.0
        imaginary = 0.0
        for n in range(num_samples):  # Sum over all time-domain samples
            angle = 2 * math.pi * k * n / num_samples
            real += signal[n] * math.cos(angle)  # Real part
            imaginary -= signal[n] * math.sin(angle)  # Imaginary part !!!
        x_result[k] = complex(real, imaginary)  # Store the complex frequency component
    return x_result

# Load the WAV file - just put the file you want to analyze into root of the project
fs, data = wavfile.read("audio.wav")

# If the file is stereo, take only one channel
if len(data.shape) > 1:
    data = data[:, 0]

# Limit data size (DFT is very slow for large arrays but you can get rid of this as well)
num_samples = 1024  # Using 1024 samples to avoid long computation time
data = data[:num_samples]

# Compute DFT
spectrum = dft_manual(data)

# Compute frequency values corresponding to the DFT output
frequencies = [(fs * k) / num_samples for k in range(num_samples)]

# Create a figure for the 2D spectrum
plt.figure(figsize=(8, 4))
plt.plot(frequencies[:num_samples//2], [abs(x) for x in spectrum[:num_samples//2]])
plt.xlabel("Frequency (Hz)")
plt.ylabel("Amplitude")
plt.title("DFT Spectrum (Manual Calculation)")
plt.show(block=False)  # Show this plot without blocking execution

# Cool and pretty 3D Spectrogram
# Let's compute it
f, t, Sxx = spectrogram(data, fs)

# Create a 3D figure
fig = plt.figure(figsize=(10, 6))
ax = fig.add_subplot(111, projection='3d')

# Create a mesh grid for X (time) and Y (frequency) axes
T, F = np.meshgrid(t, f)

# Plot the 3D surface
ax.plot_surface(F, T, 10 * np.log10(Sxx + 1e-10), cmap="jet")  # Log scale to improve visibility

# Label axes
ax.set_xlabel("Frequency (Hz)")
ax.set_ylabel("Time (sec)")
ax.set_zlabel("Magnitude (dB)")
ax.set_title("3D Spectrogram")

plt.show(block=False)

# Keep the plots open for 1000 seconds lol
plt.pause(1000)
