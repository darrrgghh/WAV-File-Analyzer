# this is code that reads a .wav file (wavfile.read()) and stores:
# fs → Sampling rate how many times per second the signal was recorded
# data → Raw audio samples (numpy array representing the waveform)
# AND PRINTS:
# The sampling rate (fs) in Hz (e.g., 44100 Hz or 48000 Hz)
# The first 10 samples of the audio waveform. You can display more if needed

import numpy as np
from scipy.io import wavfile  # Import module to read WAV files

# Load the WAV file
fs, data = wavfile.read("audio.wav")

# Define how many samples to display
num_samples = 10  # Change this to any number you want

# Print metadata and first N audio samples
print(f"Sampling Rate (fs): {fs}")  # Output the sample rate of the file
print(f"First {num_samples} samples:", data[:num_samples])  # Display the first N amplitude values
