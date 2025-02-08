import os
import wave
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import matplotlib

matplotlib.use("TkAgg")  # Используем TkAgg для работы с Tkinter
import matplotlib.pyplot as plt
import soundfile as sf
from scipy.io import wavfile
import platform
import sys
from scipy.signal import spectrogram
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from mpl_toolkits.mplot3d import Axes3D
import threading
from PIL import Image, ImageTk  # Для работы с GIF

# Подавляем предупреждения деления на ноль (например, при вычислении логарифма)
np.seterr(divide='ignore')


########################################################################
# Класс WAVAnalyzer: реализует интерфейс приложения и методы анализа  #
########################################################################

class WAVAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("WAV File Analyzer")
        # Задаём размеры главного окна
        self.root.geometry("720x270")
        self.root.minsize(720, 270)
        self.root.resizable(True, True)

        # Определяем ОС и устанавливаем иконку (файлы иконок должны быть в корне проекта)
        system = platform.system()
        if system == "Windows":
            icon_file = "1.ico"  # Файл 1.ico должен быть в корне проекта
        elif system == "Darwin":
            icon_file = "1.icns"  # Файл 1.icns должен быть в корне проекта
        else:
            icon_file = None
        if icon_file:
            icon_path = self.resource_path(icon_file)
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)

        self.data = None
        self.sample_rate = None

        # Создаём основной фрейм, разделённый на две колонки:
        # левая – для загрузки файла и кнопок,
        # правая – для отображения информации о файле.
        self.main_frame = tk.Frame(root, bg="#F5F5F5")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=2)

        # Левая колонка – загрузка файла и кнопки.
        self.left_frame = tk.Frame(self.main_frame, bg="#F5F5F5")
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        # Правая колонка – информация о файле.
        self.right_frame = tk.Frame(self.main_frame, bg="#F5F5F5")
        self.right_frame.grid(row=0, column=1, sticky="nsew")

        # Верхняя панель в левой колонке: кнопка загрузки и метка с именем файла.
        self.top_frame = tk.Frame(self.left_frame, bg="#F5F5F5")
        self.top_frame.pack(fill="x", anchor="n")
        self.load_button = ttk.Button(self.top_frame, text="📂", command=self.select_file, width=3)
        self.load_button.pack(side="left", padx=10, pady=5)
        self.file_label = tk.Label(self.top_frame, text="No file loaded", font=("Arial", 11),
                                   bg="#F5F5F5", anchor="w", width=30)
        self.file_label.pack(side="left", padx=10)

        # Создаем стиль для фиксированного размера кнопок
        self.style = ttk.Style()
        self.style.configure("Fixed.TButton", font=("Arial", 9), padding=3, width=8)

        # Панель с кнопками анализа (изначально кнопки неактивны).
        self.button_frame = tk.Frame(self.left_frame, bg="#F5F5F5")
        self.button_frame.pack(fill="x", anchor="n", padx=8, pady=8)
        self.buttons = {
            "Waveform": ttk.Button(self.button_frame, text="📈 Show Waveform", command=self.show_waveform,
                                   state="disabled", style="Fixed.TButton"),
            "Spectrogram": ttk.Button(self.button_frame, text="🎛 Show Spectrogram", command=self.show_spectrogram,
                                      state="disabled", style="Fixed.TButton"),
            "DFT": ttk.Button(self.button_frame, text="📊 Show DFT Spectrum", command=self.show_dft, state="disabled",
                              style="Fixed.TButton"),
            "3D Spectrogram": ttk.Button(self.button_frame, text="🌍 Show 3D Spectrogram",
                                         command=self.show_3d_spectrogram, state="disabled", style="Fixed.TButton"),
        }
        for button in self.buttons.values():
            button.pack(pady=4, padx=4, fill="x")

        # Правая колонка – метка для отображения информации о файле.
        self.info_label = tk.Label(self.right_frame, text="", font=("Arial", 10),
                                   bg="#F5F5F5", justify="left", anchor="nw")
        self.info_label.pack(fill="both", expand=True, padx=10, pady=5)

        # Переменная для ссылки на loading dialog (сначала отсутствует)
        self.loading_dialog = None
        # Для анимации GIF – используем оригинальный размер GIF
        self.loading_frames = []
        self.loading_frame_index = 0

    def resource_path(self, relative_path):
        """
        Возвращает абсолютный путь к ресурсу.
        Работает как при разработке, так и при компиляции с помощью PyInstaller.
        """
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)

    def select_file(self):
        """Открывает диалоговое окно для выбора WAV файла и вызывает метод анализа."""
        file_path = filedialog.askopenfilename(filetypes=[("WAV Files", "*.wav")])
        if file_path:
            self.analyze_wav(file_path)

    def get_wav_bit_depth(self, file_path):
        """Возвращает битовую глубину (бит/семпл) для указанного файла."""
        with wave.open(file_path, 'rb') as wav_file:
            sample_width = wav_file.getsampwidth()
            return sample_width * 8

    def analyze_wav(self, file_path):
        """
        Загружает WAV файл, вычисляет статистику (длительность, частота дискретизации, каналы,
        min, max, mean, RMS) и отображает эту информацию в правой колонке.
        Также включает кнопки для дальнейшего анализа.
        """
        try:
            file_name = os.path.basename(file_path)
            bit_depth = self.get_wav_bit_depth(file_path)
            try:
                sample_rate, data = wavfile.read(file_path)
                data = data.astype(np.float32) / np.max(np.abs(data))
                print("Loaded using scipy.io.wavfile")
            except Exception as e:
                print("Failed to load with scipy:", e)
                data, sample_rate = sf.read(file_path, always_2d=True)
                print("Loaded using soundfile.read")
            if data.ndim > 1:
                channels = data.shape[1]
                if channels == 1:
                    data = data[:, 0]
            else:
                channels = 1
            self.data = data
            self.sample_rate = sample_rate
            if channels == 1:
                min_val = np.min(data)
                max_val = np.max(data)
                mean_val = np.mean(data)
                rms = np.sqrt(np.mean(data ** 2))
            else:
                min_val = np.min(data, axis=0)
                max_val = np.max(data, axis=0)
                mean_val = np.mean(data, axis=0)
                rms = np.sqrt(np.mean(data ** 2, axis=0))
            if channels == 1:
                channel_info = "Mono"
                stats_str = (
                    f"🔎Min: {min_val:.4f}\n"
                    f"🔎Max: {max_val:.4f}\n"
                    f"📉Mean: {mean_val:.4f}, RMS: {rms:.4f}"
                )
            else:
                channel_info = "Stereo" if channels == 2 else f"{channels} channels"
                stats_str = ""
                for i in range(channels):
                    stats_str += (
                        f"Channel {i + 1}:\n"
                        f"🔎Min: {min_val[i]:.4f}, Max: {max_val[i]:.4f}\n"
                        f"📉Mean: {mean_val[i]:.4f}, RMS: {rms[i]:.4f}\n"
                    )
            self.file_label.config(text=f"📂 {file_name}")
            self.info_label.config(
                text=f"🎵Sample rate: {sample_rate} Hz\n"
                     f"📝Bit depth: {bit_depth}-bit\n"
                    f"⌛Duration: {data.shape[0] / sample_rate:.2f} sec\n"
                     f"🔊Channels: {channel_info}\n"
                     f"{stats_str}"
            )
            for button in self.buttons.values():
                button.config(state="normal")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process the file!\n{str(e)}")

    def check_data(self):
        """Проверяет, загружены ли аудиоданные."""
        if self.data is None:
            messagebox.showerror("Error", "Please load a WAV file first!")
            return False
        return True

    #################################################
    # Методы для отображения loading dialog         #
    #################################################

    def show_loading_dialog(self):
        """
        Создаёт модальное окно loading dialog с анимированным GIF (loading.gif),
        отображаемое в центре всего экрана.
        Используется оригинальный размер GIF.
        Задержка 1500 мс перед показом графика, чтобы проигрались хотя бы 15 кадров.
        """
        self.loading_dialog = tk.Toplevel(self.root)
        self.loading_dialog.overrideredirect(True)
        # Устанавливаем фон окна равным чёрному, а затем делаем его прозрачным
        self.loading_dialog.configure(bg="black")
        self.loading_dialog.attributes("-topmost", True)
        gif_path = self.resource_path("loading.gif")
        if os.path.exists(gif_path):
            try:
                self.loading_gif = Image.open(gif_path)
                orig_size = self.loading_gif.size  # (width, height)
                # print("Original GIF size:", orig_size)
                self.loading_frames = []
                try:
                    while True:
                        # Загружаем кадр без изменения – сохраняем оригинальное изображение
                        frame = self.loading_gif.copy()
                        self.loading_frames.append(ImageTk.PhotoImage(frame))
                        self.loading_gif.seek(len(self.loading_frames))
                except EOFError:
                    pass
                # print("Total GIF frames loaded:", len(self.loading_frames))
                if self.loading_frames:
                    self.loading_frame_index = 0
                    # Устанавливаем размер окна равным оригинальному размеру GIF
                    width, height = orig_size
                    screen_width = self.root.winfo_screenwidth()
                    screen_height = self.root.winfo_screenheight()
                    x = (screen_width // 2) - (width // 2)
                    y = (screen_height // 2) - (height // 2)
                    self.loading_dialog.geometry(f"{width}x{height}+{x}+{y}")
                    # Делаем чёрный цвет прозрачным
                    self.loading_dialog.wm_attributes("-transparentcolor", "black")
                    self.loading_label = tk.Label(self.loading_dialog, bg="black")
                    self.loading_label.pack(expand=True)
                    self.animate_loading_gif()
                else:
                    raise Exception("No frames found in GIF")
            except Exception as e:
                print("Error loading GIF:", e)
                self.loading_label = tk.Label(self.loading_dialog, text="Loading...", fg="lime", bg="black",
                                              font=("Courier", 14))
                self.loading_label.pack(expand=True)
        else:
            print("loading.gif not found, using fallback text.")
            self.loading_label = tk.Label(self.loading_dialog, text="Loading...", fg="lime", bg="black",
                                          font=("Courier", 14))
            self.loading_label.pack(expand=True)

    def animate_loading_gif(self):
        """Обновляет кадр анимированного GIF каждые 100 мс. Отладочный вывод: кадр и общее количество кадров."""
        if self.loading_dialog is None or not self.loading_frames:
            return
        # print(f"Animating frame {self.loading_frame_index + 1} of {len(self.loading_frames)}")
        frame = self.loading_frames[self.loading_frame_index]
        self.loading_label.configure(image=frame)
        self.loading_label.image = frame
        self.loading_frame_index = (self.loading_frame_index + 1) % len(self.loading_frames)
        self.loading_dialog.after(100, self.animate_loading_gif)

    def hide_loading_dialog(self):
        """Закрывает окно loading dialog. (Отладочный вывод: закрыто)"""
        if self.loading_dialog is not None:
            print("Hiding loading dialog")
            self.loading_dialog.destroy()
            self.loading_dialog = None

    #################################################
    # Функции для отображения графиков              #
    # (Все операции выполняются в главном потоке)    #
    #################################################

    def _display_figure(self, fig, title="Plot"):
        """
        Создаёт новое окно (Toplevel) и встраивает в него фигуру matplotlib.
        Добавляет панель инструментов (toolbar) для сохранения и управления графиком.
        Задержка 1500 мс перед показом графика, чтобы проигрались хотя бы 15 кадров.
        """

        def show_it():
            win = tk.Toplevel(self.root)
            win.title(title)
            canvas = FigureCanvasTkAgg(fig, master=win)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            toolbar = NavigationToolbar2Tk(canvas, win)
            toolbar.update()
            toolbar.pack(side=tk.TOP, fill=tk.X)
            self.hide_loading_dialog()

        self.root.after(1500, show_it)

    def show_waveform(self):
        """Отображает график waveform (форма сигнала) с помощью matplotlib."""
        if not self.check_data():
            return
        self.show_loading_dialog()
        if self.data.ndim == 1:
            fig, ax = plt.subplots(figsize=(8, 4))
            time = np.linspace(0, len(self.data) / self.sample_rate, num=len(self.data))
            ax.plot(time, self.data, color='blue')
            ax.set_title("Waveform (Mono)")
            ax.set_xlabel("Time (sec)")
            ax.set_ylabel("Amplitude")
            ax.grid()
        else:
            n_channels = self.data.shape[1]
            fig, axs = plt.subplots(n_channels, 1, figsize=(8, 3 * n_channels), sharex=True)
            if n_channels == 1:
                axs = [axs]
            time = np.linspace(0, self.data.shape[0] / self.sample_rate, num=self.data.shape[0])
            colors = ['blue', 'red', 'green', 'orange']
            for i in range(n_channels):
                axs[i].plot(time, self.data[:, i], color=colors[i % len(colors)])
                axs[i].set_title(f"Channel {i + 1} Waveform")
                axs[i].set_ylabel("Amplitude")
                axs[i].grid()
            axs[-1].set_xlabel("Time (sec)")
        self._display_figure(fig, "Waveform")

    def show_spectrogram(self):
        """Отображает 2D спектрограмму аудиофайла с помощью matplotlib."""
        if not self.check_data():
            return
        self.show_loading_dialog()
        if self.data.ndim == 1:
            fig, ax = plt.subplots(figsize=(8, 4))
            Pxx, freqs, bins, im = ax.specgram(self.data, Fs=self.sample_rate, cmap='inferno',
                                               NFFT=2048, noverlap=1024)
            Pxx = np.log10(Pxx + 1e-10)
            Pxx = (Pxx - np.min(Pxx)) / (np.max(Pxx) - np.min(Pxx) + 1e-10)
            ax.imshow(Pxx, aspect='auto', extent=[bins.min(), bins.max(), freqs.min(), freqs.max()],
                      origin='lower', cmap='magma')
            ax.set_title("Spectrogram (Mono)")
            ax.set_xlabel("Time (sec)")
            ax.set_ylabel("Frequency (Hz)")
        else:
            n_channels = self.data.shape[1]
            fig, axs = plt.subplots(n_channels, 1, figsize=(8, 4 * n_channels))
            if n_channels == 1:
                axs = [axs]
            for i in range(n_channels):
                channel_data = self.data[:, i]
                Pxx, freqs, bins, im = axs[i].specgram(channel_data, Fs=self.sample_rate, cmap='inferno',
                                                       NFFT=2048, noverlap=1024)
                Pxx = np.log10(Pxx + 1e-10)
                Pxx = (Pxx - np.min(Pxx)) / (np.max(Pxx) - np.min(Pxx) + 1e-10)
                axs[i].imshow(Pxx, aspect='auto', extent=[bins.min(), bins.max(), freqs.min(), freqs.max()],
                              origin='lower', cmap='magma')
                axs[i].set_title(f"Spectrogram - Channel {i + 1}")
                axs[i].set_ylabel("Frequency (Hz)")
            axs[-1].set_xlabel("Time (sec)")
        self._display_figure(fig, "Spectrogram")

    def show_dft(self):
        """Отображает спектр DFT аудиофайла с помощью matplotlib.
           Для стереофайлов спектры каждого канала выводятся в один ряд."""
        if not self.check_data():
            return
        self.show_loading_dialog()
        if self.data.ndim == 1:
            spectrum = np.fft.fft(self.data)
            frequencies = np.fft.fftfreq(len(self.data), d=1 / self.sample_rate)
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.plot(frequencies[:len(frequencies) // 2], np.abs(spectrum[:len(frequencies) // 2]), color='purple')
            ax.set_title("DFT Spectrum (Mono)")
            ax.set_xlabel("Frequency (Hz)")
            ax.set_ylabel("Amplitude")
            ax.grid()
        else:
            n_channels = self.data.shape[1]
            fig, axs = plt.subplots(1, n_channels, figsize=(8 * n_channels, 4))
            if n_channels == 1:
                axs = [axs]
            frequencies = np.fft.fftfreq(self.data.shape[0], d=1 / self.sample_rate)
            for i in range(n_channels):
                spectrum = np.fft.fft(self.data[:, i])
                axs[i].plot(frequencies[:len(frequencies) // 2],
                            np.abs(spectrum[:len(frequencies) // 2]),
                            color='purple')
                axs[i].set_title(f"DFT Spectrum - Channel {i + 1}")
                axs[i].set_xlabel("Frequency (Hz)")
                axs[i].set_ylabel("Amplitude")
                axs[i].grid()
            axs[-1].set_xlabel("Frequency (Hz)")
        self._display_figure(fig, "DFT Spectrum")

    def show_3d_spectrogram(self):
        """Отображает 3D спектрограмму аудиофайла с помощью matplotlib.
           Для стереофайлов для каждого канала создаются 3D графики в один ряд."""
        if not self.check_data():
            return
        self.show_loading_dialog()
        if self.data.ndim == 1:
            nperseg = min(2048, len(self.data) // 10)
            f, t, Sxx = spectrogram(self.data, self.sample_rate, nperseg=nperseg)
            T, F = np.meshgrid(t, f)
            fig = plt.figure(figsize=(8, 6))
            ax = fig.add_subplot(111, projection='3d')
            ax.plot_surface(T, F, 10 * np.log10(Sxx + 1e-10), cmap="jet")
            ax.set_xlabel("Time (sec)")
            ax.set_ylabel("Frequency (Hz)")
            ax.set_zlabel("Magnitude (dB)")
            ax.set_title("3D Spectrogram (Mono)")
        else:
            n_channels = self.data.shape[1]
            fig = plt.figure(figsize=(8 * n_channels, 6))
            for i in range(n_channels):
                nperseg = min(2048, self.data.shape[0] // 10)
                f, t, Sxx = spectrogram(self.data[:, i], self.sample_rate, nperseg=nperseg)
                ax = fig.add_subplot(1, n_channels, i + 1, projection='3d')
                T, F = np.meshgrid(t, f)
                ax.plot_surface(T, F, 10 * np.log10(Sxx + 1e-10), cmap="jet")
                ax.set_xlabel("Time (sec)")
                ax.set_ylabel("Frequency (Hz)")
                ax.set_zlabel("Magnitude (dB)")
                ax.set_title(f"3D Spectrogram (Channel {i + 1})")
        self._display_figure(fig, "3D Spectrogram")


########################################################################
# Splash Screen: отображает логотип перед загрузкой основного окна     #
########################################################################

def show_splash(root, duration=4000):
    """
    Отображает splash screen с логотипом.
    :param root: Главное окно приложения (Tk).
    :param duration: Время показа splash screen в миллисекундах (здесь 4000 = 4 секунды).
    """
    splash = tk.Toplevel(root)
    splash.overrideredirect(True)  # Убираем рамки окна
    splash.config(bg="#F5F5F5")
    logo_path = os.path.join(sys._MEIPASS, "logo.png") if hasattr(sys, '_MEIPASS') else os.path.join(os.path.abspath("."), "logo.png")
    if os.path.exists(logo_path):
        splash_image = tk.PhotoImage(file=logo_path).subsample(2, 2)
        splash_label = tk.Label(splash, image=splash_image, bg="#F5F5F5")
        splash_label.image = splash_image  # сохраняем ссылку
        splash_label.pack()
    else:
        splash_label = tk.Label(splash, text="WAV File Analyzer", font=("Arial", 24), bg="#F5F5F5")
        splash_label.pack(padx=20, pady=20)
    splash.update_idletasks()
    width = splash.winfo_width()
    height = splash.winfo_height()
    screen_width = splash.winfo_screenwidth()
    screen_height = splash.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    splash.geometry(f"{width}x{height}+{x}+{y}")
    root.after(duration, splash.destroy)


########################################################################
# Основной блок: создание главного окна, отображение splash screen и запуск #
########################################################################

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Скрываем главное окно
    show_splash(root, duration=2000)  # Показываем splash screen на 2 секунды
    root.after(2000, root.deiconify)  # После 2 секунд показываем главное окно
    app = WAVAnalyzer(root)
    root.mainloop()
# use pyinstaller to make executable file
# run on Windows
# pyinstaller --onefile --windowed --icon=1.ico --add-data "loading.gif;." --add-data "logo.png;." --add-data "1.ico;." wav_analyzer.py
# run on Mac
# pyinstaller --onefile --windowed --icon=1.icns --add-data "loading.gif:." --add-data "logo.png:." --add-data "1.icns:." wav_analyzer.py

