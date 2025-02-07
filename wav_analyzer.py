import os
import wave
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import matplotlib.pyplot as plt
import soundfile as sf
from scipy.io import wavfile
from scipy.signal import spectrogram
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d import Axes3D


class WAVAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("WAV File Analyzer")
        self.root.geometry("600x350")  # Уменьшил высоту стартового окна
        self.root.minsize(500, 300)  # Минимальный размер
        self.root.resizable(True, True)  # Теперь можно растягивать окно

        self.data = None
        self.sample_rate = None

        # Главное окно
        self.main_frame = tk.Frame(root, bg="#F5F5F5")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Верхняя панель с кнопкой загрузки
        self.top_frame = tk.Frame(self.main_frame, bg="#F5F5F5")
        self.top_frame.pack(fill="x")

        # Кнопка с иконкой 📂 (папка)
        self.load_button = ttk.Button(self.top_frame, text="📂", command=self.select_file, width=3)
        self.load_button.pack(side="left", padx=10)

        # Название загруженного файла
        self.file_label = tk.Label(self.top_frame, text="No file loaded", font=("Arial", 12), bg="#F5F5F5")
        self.file_label.pack(side="left", padx=10)

        # Информация о файле
        self.info_label = tk.Label(self.main_frame, text="", font=("Arial", 10), bg="#F5F5F5", justify="left")
        self.info_label.pack(fill="x", padx=10, pady=5)

        # Кнопки для анализа
        self.button_frame = tk.Frame(self.main_frame, bg="#F5F5F5")
        self.button_frame.pack(fill="both", padx=10, pady=10)

        self.buttons = {
            "Waveform": ttk.Button(self.button_frame, text="📈 Show Waveform", command=self.show_waveform, state="disabled"),
            "Spectrogram": ttk.Button(self.button_frame, text="🎛 Show Spectrogram", command=self.show_spectrogram, state="disabled"),
            "DFT": ttk.Button(self.button_frame, text="📊 Show DFT Spectrum", command=self.show_dft, state="disabled"),
            "3D Spectrogram": ttk.Button(self.button_frame, text="🌍 Show 3D Spectrogram", command=self.show_3d_spectrogram, state="disabled"),
        }

        for button in self.buttons.values():
            button.pack(pady=5, fill="x")



    def select_file(self):
        """ Opens a file dialog and loads WAV file. """
        file_path = filedialog.askopenfilename(filetypes=[("WAV Files", "*.wav")])
        if file_path:
            self.analyze_wav(file_path)

    def get_wav_bit_depth(self, file_path):
        """Определяет битность WAV файла."""
        with wave.open(file_path, 'rb') as wav_file:
            sample_width = wav_file.getsampwidth()  # Получаем ширину семпла в байтах
            bit_depth = sample_width * 8  # Конвертируем в биты (8 бит на байт)
            return bit_depth

    def analyze_wav(self, file_path):
        """ Reads the WAV file and updates the UI. """
        try:
            file_name = os.path.basename(file_path)

            # Извлекаем битность WAV-файла
            bit_depth = bit_depth = self.get_wav_bit_depth(file_path)


            # Load WAV file
            try:
                sample_rate, data = wavfile.read(file_path)
                data = data.astype(np.float32) / np.max(np.abs(data))
                print("Loaded using scipy.io.wavfile")
            except Exception as e:
                print("Failed to load with scipy:", e)
                data, sample_rate = sf.read(file_path, always_2d=True)
                print("Loaded using soundfile.read")

            if len(data.shape) > 1 and data.shape[1] > 1:
                data = data.mean(axis=1)  # Convert to mono

            self.data = data
            self.sample_rate = sample_rate

            min_val, max_val = np.min(data), np.max(data)
            mean_val = np.mean(data)
            rms = np.sqrt(np.mean(data ** 2))

            # Обновляем интерфейс
            self.file_label.config(text=f"📂 {file_name}")
            self.info_label.config(
                text=f"🎵 Sample rate: {sample_rate} Hz\n"
                     f"📝 Bit depth: {bit_depth}-bit\n"  # Вернули битность
                     f"⏳ Duration: {len(data) / sample_rate:.2f} sec\n"
                     f"🔎 Min: {min_val:.4f}, Max: {max_val:.4f}\n"
                     f"📉 Mean: {mean_val:.4f}, RMS: {rms:.4f}"
            )

            # Включаем кнопки
            for button in self.buttons.values():
                button.config(state="normal")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to process the file!\n{str(e)}")

    def check_data(self):
        """ Проверяет, загружены ли данные перед построением графиков. """
        if self.data is None:
            messagebox.showerror("Error", "Please load a WAV file first!")
            return False
        return True

    def show_waveform(self):
        if not self.check_data():
            return
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(np.linspace(0, len(self.data) / self.sample_rate, num=len(self.data)), self.data, color='blue')
        ax.set_title("Waveform")
        ax.set_xlabel("Time (sec)")
        ax.set_ylabel("Amplitude")
        ax.grid()
        plt.show()

    def show_spectrogram(self):
        if not self.check_data():
            return

        fig, ax = plt.subplots(figsize=(8, 4))

        # Вычисляем спектрограмму
        Pxx, freqs, bins, im = ax.specgram(self.data, Fs=self.sample_rate, cmap='inferno', NFFT=2048, noverlap=1024)

        # Добавляем маленькое число, чтобы избежать log10(0)
        Pxx = np.log10(Pxx + 1e-10)

        # Нормализация, чтобы не было слишком темных участков
        Pxx = (Pxx - np.min(Pxx)) / (np.max(Pxx) - np.min(Pxx))  # Приводим значения к диапазону [0, 1]

        # Отображаем спектрограмму с нормализованными значениями
        ax.imshow(Pxx, aspect='auto', extent=[bins.min(), bins.max(), freqs.min(), freqs.max()], origin='lower',
                  cmap='magma')

        ax.set_title("Spectrogram")
        ax.set_xlabel("Time (sec)")
        ax.set_ylabel("Frequency (Hz)")
        plt.show()

    def show_dft(self):
        if not self.check_data():
            return
        spectrum = np.fft.fft(self.data)
        frequencies = np.fft.fftfreq(len(self.data), d=1 / self.sample_rate)
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(frequencies[:len(frequencies) // 2], np.abs(spectrum[:len(frequencies) // 2]), color='purple')
        ax.set_title("DFT Spectrum")
        ax.set_xlabel("Frequency (Hz)")
        ax.set_ylabel("Amplitude")
        ax.grid()
        plt.show()

    def show_3d_spectrogram(self):
        if not self.check_data():
            return
        nperseg = min(2048, len(self.data) // 10)
        f, t, Sxx = spectrogram(self.data, self.sample_rate, nperseg=nperseg)
        T, F = np.meshgrid(t, f)

        fig = plt.figure(figsize=(8, 6))
        ax = fig.add_subplot(111, projection='3d')
        ax.plot_surface(T, F, 10 * np.log10(Sxx + 1e-10), cmap="jet")
        ax.set_xlabel("Time (sec)")
        ax.set_ylabel("Frequency (Hz)")
        ax.set_zlabel("Magnitude (dB)")
        ax.set_title("3D Spectrogram")
        plt.show()


# Запуск GUI
root = tk.Tk()
app = WAVAnalyzer(root)
root.mainloop()
