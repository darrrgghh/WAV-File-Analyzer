import wave
import math
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import matplotlib.pyplot as plt
import soundfile as sf
from scipy.io import wavfile
from scipy.signal import spectrogram
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d import Axes3D


def dft_manual(signal):
    """ Compute the Discrete Fourier Transform (DFT) manually. """
    num_samples = len(signal)
    x_result = [0] * num_samples
    for k in range(num_samples):
        real = 0.0
        imaginary = 0.0
        for n in range(num_samples):
            angle = 2 * math.pi * k * n / num_samples
            real += signal[n] * math.cos(angle)
            imaginary -= signal[n] * math.sin(angle)
        x_result[k] = complex(real, imaginary)
    return x_result


def open_waveform(data, duration):
    """ Open a new window for the waveform plot. """
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(np.linspace(0, duration, num=len(data)), data, color='blue')
    ax.set_title("Waveform")
    ax.set_xlabel("Time (sec)")
    ax.set_ylabel("Amplitude")
    ax.grid()
    plt.show()


def open_spectrogram(data, sample_rate):
    """ Open a new window for the spectrogram plot. """
    fig, ax = plt.subplots(figsize=(8, 4))
    spec, freq, t, im = ax.specgram(data.flatten(), Fs=sample_rate, cmap='inferno')
    ax.set_title("Spectrogram")
    ax.set_xlabel("Time (sec)")
    ax.set_ylabel("Frequency (Hz)")
    plt.show()


def open_dft_spectrum(data, sample_rate):
    """ Open a new window for the DFT spectrum plot. """
    num_samples = 1024
    signal = data[:num_samples]
    spectrum = dft_manual(signal)
    frequencies = [(sample_rate * k) / num_samples for k in range(num_samples)]

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(frequencies[:num_samples // 2], [abs(x) for x in spectrum[:num_samples // 2]], color='purple')
    ax.set_title("DFT Spectrum")
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Amplitude")
    ax.grid()
    plt.show()


def open_3d_spectrogram(data, sample_rate):
    """ Open a new window for the 3D spectrogram plot. """
    num_samples = 1024
    signal = data[:num_samples]

    f, t, Sxx = spectrogram(signal, sample_rate)
    T, F = np.meshgrid(t, f)

    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection='3d')
    ax.plot_surface(F, T, 10 * np.log10(Sxx + 1e-10), cmap="jet")
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Time (sec)")
    ax.set_zlabel("Magnitude (dB)")
    ax.set_title("3D Spectrogram")
    plt.show()


def analyze_wav(file_path, root):
    """ Reads the WAV file and sets up buttons to open graphs. """
    try:
        with wave.open(file_path, 'rb') as wav_file:
            num_channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            sample_rate = wav_file.getframerate()
            num_frames = wav_file.getnframes()
            duration = num_frames / sample_rate
            bit_depth = sample_width * 8

        data, _ = sf.read(file_path, always_2d=True)

        if data.shape[1] > 1:
            data = data.mean(axis=1)

        min_val, max_val = np.min(data), np.max(data)
        mean_val = np.mean(data)
        rms = np.sqrt(np.mean(data ** 2))

        # Clear previous UI elements
        for widget in root.winfo_children():
            if isinstance(widget, tk.Label) or isinstance(widget, ttk.Button):
                widget.destroy()

        info_text = f"📂 File: {file_path}\n" \
                    f"🎵 Channels: {num_channels}\n" \
                    f"📊 Sample rate: {sample_rate} Hz\n" \
                    f"📝 Bit depth: {bit_depth} bits\n" \
                    f"⏳ Duration: {duration:.2f} sec\n" \
                    f"🔎 Min: {min_val}, Max: {max_val}\n" \
                    f"📉 Mean: {mean_val:.2f}, RMS: {rms:.2f}\n"
        label = tk.Label(root, text=info_text, justify="left", font=("Arial", 10), bg="#F5F5F5", padx=10, pady=10)
        label.pack(fill="x", padx=20, pady=10)

        # Frame for buttons
        button_frame = tk.Frame(root, bg="#F5F5F5")
        button_frame.pack(fill="both", padx=20, pady=10)

        # Define a ttk style
        style = ttk.Style()
        style.configure("TButton", font=("Arial", 10), padding=5)

        # Buttons with minimal UI style
        ttk.Button(button_frame, text="📈 Show Waveform", command=lambda: open_waveform(data, duration),
                   style="TButton").pack(pady=5, fill="x")
        ttk.Button(button_frame, text="🎛 Show Spectrogram", command=lambda: open_spectrogram(data, sample_rate),
                   style="TButton").pack(pady=5, fill="x")
        ttk.Button(button_frame, text="📊 Show DFT Spectrum", command=lambda: open_dft_spectrum(data, sample_rate),
                   style="TButton").pack(pady=5, fill="x")
        ttk.Button(button_frame, text="🌍 Show 3D Spectrogram", command=lambda: open_3d_spectrogram(data, sample_rate),
                   style="TButton").pack(pady=5, fill="x")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to process the file!\n{str(e)}")


def select_file(root):
    """ Opens a file dialog and triggers file analysis. """
    file_path = filedialog.askopenfilename(filetypes=[("WAV Files", "*.wav")])
    if file_path:
        analyze_wav(file_path, root)


# Launch GUI
root = tk.Tk()
root.title("WAV File Analyzer")
root.geometry("500x400")  # Increased starting size
root.minsize(500, 400)
root.configure(bg="#F5F5F5")  # Light gray background for modern look

# Define a ttk style for the main button
style = ttk.Style()
style.configure("TButton", font=("Arial", 12), padding=5)

btn = ttk.Button(root, text="📂 Select WAV File", command=lambda: select_file(root), style="TButton")
btn.pack(pady=20, padx=20)

root.mainloop()
