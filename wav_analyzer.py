import os
import wave
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

import soundfile as sf
from scipy.io import wavfile
import platform
import sys
from scipy.signal import spectrogram
from pydub import AudioSegment
from PIL import Image, ImageTk

# === Изменение: добавляем simpleaudio для воспроизведения ===
import simpleaudio as sa

np.seterr(divide='ignore')  # подавляем предупреждения деления на ноль

class SoundAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("Sound Analyzer 0.3")

        # Задаём «базовый» размер окна
        self.root.geometry("1000x600")
        self.root.minsize(800, 500)
        self.root.resizable(True, True)

        # Установка иконки (если нужно)
        system = platform.system()
        if system == "Windows":
            icon_file = "1.ico"
        elif system == "Darwin":
            icon_file = "1.icns"
        else:
            icon_file = None
        if icon_file:
            icon_path = self.resource_path(icon_file)
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
                self.icon_path = icon_path  # сохраняем путь к иконке

        self.data = None
        self.sample_rate = None

        # Переменные для анимации загрузки
        self.loading_dialog = None
        self.loading_frames = []
        self.loading_frame_index = 0

        # Флаг для режима real-time
        self.realtime_mode = False

        # Переменные для воспроизведения
        self.audio_segment = None  # хранит AudioSegment для всех форматов
        self.play_obj = None  # объект воспроизведения из simpleaudio
        self.is_playing = False
        self.current_frame = 0  # текущая позиция в сэмплах (индекс)

        # Флаг для отслеживания перетаскивания ползунка позиции
        self.is_dragging = False

        # Храним идентификатор after() для отмены старых циклов
        self.update_handle = None

        # -------------- Меню --------------
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Load File", command=self.select_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About...", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

        # ---------- Основной фрейм (левая и правая части) ----------
        self.main_frame = tk.Frame(self.root, bg="#F5F5F5")
        self.main_frame.pack(fill="both", expand=True)

        self.main_frame.columnconfigure(0, weight=0)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(0, weight=1)

        # ---------- Левая панель ----------
        self.left_frame = tk.Frame(self.main_frame, bg="#F5F5F5", width=250)
        self.left_frame.grid(row=0, column=0, sticky="ns")
        self.left_frame.grid_propagate(False)

        # Верхняя панель: кнопка "Load File" и метка статуса
        self.top_frame = tk.Frame(self.left_frame, bg="#F5F5F5")
        self.top_frame.pack(fill="x", anchor="n", pady=5)

        self.load_button = ttk.Button(
            self.top_frame,
            text="📂",
            command=self.select_file,
            width=3
        )
        self.load_button.pack(side="left", padx=5)

        self.file_label = tk.Label(
            self.top_frame,
            text="No file loaded",
            font=("Arial", 11),
            bg="#F5F5F5",
            anchor="w",
            width=16
        )
        self.file_label.pack(side="left", padx=5)

        # Кнопки анализа
        self.button_frame = tk.Frame(self.left_frame, bg="#F5F5F5")
        self.button_frame.pack(fill="x", anchor="n", padx=10, pady=10)

        self.style = ttk.Style()
        self.style.configure("Fixed.TButton", font=("Arial", 9), padding=3, width=25)
        # Создаем отдельный стиль для Real-time кнопки
        self.style.configure("RealTime.TButton", font=("Arial", 9), padding=3, width=25, foreground="red")

        self.buttons = {
            "Waveform": ttk.Button(self.button_frame, text="📈 Show Waveform",
                                   command=self.show_waveform, state="disabled", style="Fixed.TButton"),
            "Spectrogram": ttk.Button(self.button_frame, text="🎛 Show Spectrogram",
                                      command=self.show_spectrogram, state="disabled", style="Fixed.TButton"),
            "3D Spectrogram": ttk.Button(self.button_frame, text="🌍 Show 3D Spectrogram",
                                         command=self.show_3d_spectrogram, state="disabled", style="Fixed.TButton"),
            "DFT": ttk.Button(self.button_frame, text="📊 Show DFT Spectrum",
                              command=self.show_dft, state="disabled", style="Fixed.TButton")
        }
        for btn in self.buttons.values():
            btn.pack(pady=4, fill="x")

        # Метка с информацией о файле
        self.info_label = tk.Label(
            self.left_frame,
            text="",
            font=("Arial", 10),
            bg="#F5F5F5",
            justify="left",
            anchor="nw",
            wraplength=220
        )
        self.info_label.pack(fill="both", expand=True, padx=10, pady=5)

        # Кнопка для включения Real-time с использованием стиля "RealTime.TButton"
        self.realtime_button = ttk.Button(
            self.left_frame,
            text="Real-time OFF",
            command=self.toggle_realtime,
            style="RealTime.TButton"
        )
        self.realtime_button.pack(side="bottom", pady=10)

        # ---------- Правая панель (placeholder + графики) ----------
        self.right_frame = tk.Frame(self.main_frame, bg="white")
        self.right_frame.grid(row=0, column=1, sticky="nsew")
        self.right_frame.rowconfigure(0, weight=1)
        self.right_frame.columnconfigure(0, weight=1)

        # Создаем placeholder Label с изображением
        placeholder_path = self.resource_path("placeholder.png")
        if os.path.exists(placeholder_path):
            self.placeholder_img = tk.PhotoImage(file=placeholder_path)
            self.placeholder_label = tk.Label(self.right_frame, image=self.placeholder_img, bg="white")
            self.placeholder_label.pack(fill="both", expand=True)
        else:
            self.placeholder_label = tk.Label(self.right_frame, text="Welcome!\nPlease load a file to display graphs.",
                                              font=("Arial", 14), bg="white")
            self.placeholder_label.pack(fill="both", expand=True)

        # ---------- Панель воспроизведения (playback controls) ----------
        self.playback_frame = tk.Frame(self.root, bg="#F5F5F5", height=40)
        self.playback_frame.pack(side="bottom", fill="x")

        # 1) Кнопка Play/Pause (кнопка запуска или паузы)
        self.play_pause_button = ttk.Button(self.playback_frame, text="▶", command=self.on_play_pause)
        self.play_pause_button.pack(side="left", padx=5, pady=5)

        # 2) Кнопка Stop (останавливает воспроизведение и возвращает ползунок в начало)
        self.stop_button = ttk.Button(self.playback_frame, text="■", command=self.on_stop)
        self.stop_button.pack(side="left", padx=5, pady=5)

        # Флаг, показывающий, на паузе ли трек
        self.is_paused = False

        # --- Создаём вложенный фрейм, в котором будут находиться метки времени и ползунок ---
        # Благодаря expand=True, fill="x", этот фрейм будет растягиваться при изменении размера окна.
        progress_frame = tk.Frame(self.playback_frame, bg="#F5F5F5")
        progress_frame.pack(side="left", expand=True, fill="x")

        # Метка для текущего времени (слева от ползунка)
        self.current_time_label = tk.Label(progress_frame, text="0:00", bg="#F5F5F5")
        self.current_time_label.pack(side="left", padx=5)

        # Ползунок прогресса, который будет занимать всё доступное пространство между двумя метками времени
        self.position_var = tk.DoubleVar()
        self.position_scale = ttk.Scale(
            progress_frame,
            from_=0,
            to=100,
            orient="horizontal",
            length=250,  # Можно поменять это значение, чтобы задать «базовую» ширину
            variable=self.position_var
        )
        self.position_scale.pack(side="left", expand=True, fill="x", padx=5, pady=5)

        # Привязываем обработчики нажатия, перемещения и отпускания мыши
        self.position_scale.bind("<Button-1>", self._on_scale_press)  # При нажатии (одиночный клик)
        self.position_scale.bind("<B1-Motion>", self._on_scale_drag)  # При «протягивании» ползунка
        self.position_scale.bind("<ButtonRelease-1>", self._on_scale_release)  # Когда кнопку отпустили

        # Метка для оставшегося времени (справа от ползунка)
        self.remaining_time_label = tk.Label(progress_frame, text="-0:00", bg="#F5F5F5")
        self.remaining_time_label.pack(side="left", padx=5)

        # Метка "Volume:" и слайдер громкости располагаем в самой playback_frame,
        # чтобы они были справа от всего «прогресс‐фрейма»
        tk.Label(self.playback_frame, text="Volume:", bg="#F5F5F5").pack(side="left", padx=5)
        self.volume_scale = ttk.Scale(self.playback_frame, from_=0, to=100, orient="horizontal")
        self.volume_scale.set(70)
        self.volume_scale.pack(side="left", padx=5, pady=5)
        self.volume_scale.bind("<ButtonRelease-1>", self._on_volume_change)

        # Обработчик закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        self.hide_loading_dialog()
        self.root.destroy()
        sys.exit(0)

    # ==================== Методы воспроизведения ====================
    def on_play_pause(self):
        """
        Если трек не играет и не на паузе — начать воспроизведение.
        Если трек играет — поставить на паузу.
        Если трек на паузе — возобновить.
        """
        if self.data is None:
            messagebox.showerror("Error", "Please load an audio file first!")
            return

        # 1) Если не играет и не на паузе — старт
        if not self.is_playing and not self.is_paused:
            self._start_playback()
        # 2) Если играет — пауза
        elif self.is_playing:
            self._pause_playback()
        # 3) Если на паузе — возобновляем
        else:
            self._resume_playback()

    def _start_playback(self):
        """Начинаем воспроизведение с текущего current_frame."""
        if self.update_handle is not None:
            self.root.after_cancel(self.update_handle)
            self.update_handle = None

        self.is_playing = True
        self.is_paused = False

        if self.current_frame >= len(self.data):
            self.current_frame = 0

        volume_factor = self.volume_scale.get() / 100.0
        segment_to_play = self.data[self.current_frame:] * volume_factor
        segment_to_play = segment_to_play.astype(np.float32)

        self.play_obj = sa.play_buffer(
            segment_to_play.tobytes(),
            1 if segment_to_play.ndim == 1 else segment_to_play.shape[1],
            4,
            self.sample_rate
        )

        # Меняем текст кнопки на «⏸»
        self.play_pause_button.config(text="⏸")
        self.update_scale_position()

    def _pause_playback(self):
        """Ставим на паузу (остановить play_obj, но current_frame не сбрасываем)."""
        if self.play_obj is not None:
            self.play_obj.stop()
            self.play_obj = None

        self.is_playing = False
        self.is_paused = True
        # Меняем текст кнопки на «▶»
        self.play_pause_button.config(text="▶")

    def _resume_playback(self):
        """Возобновляем с current_frame."""
        if self.update_handle is not None:
            self.root.after_cancel(self.update_handle)
            self.update_handle = None

        self.is_playing = True
        self.is_paused = False

        volume_factor = self.volume_scale.get() / 100.0
        segment_to_play = self.data[self.current_frame:] * volume_factor
        segment_to_play = segment_to_play.astype(np.float32)

        self.play_obj = sa.play_buffer(
            segment_to_play.tobytes(),
            1 if segment_to_play.ndim == 1 else segment_to_play.shape[1],
            4,
            self.sample_rate
        )

        self.play_pause_button.config(text="⏸")
        self.update_scale_position()

    def on_stop(self):
        """
        Останавливает воспроизведение и сбрасывает current_frame в начало (0).
        """
        if self.play_obj:
            self.play_obj.stop()
            self.play_obj = None
        self.is_playing = False
        self.is_paused = False
        self.current_frame = 0
        self.position_var.set(0)

        # Меняем кнопку на «▶»
        self.play_pause_button.config(text="▶")

    def update_scale_position(self):
        if not self.is_playing or self.is_dragging:
            return

        frames_per_update = int(self.sample_rate * 0.1)
        self.current_frame += frames_per_update

        total_frames = len(self.data)
        if self.current_frame >= total_frames:
            self.on_stop()
            return

        progress_percent = (self.current_frame / total_frames) * 100
        self.position_var.set(progress_percent)

        # --- Обновляем время ---
        current_sec = self.current_frame / self.sample_rate
        total_sec = total_frames / self.sample_rate
        remain_sec = total_sec - current_sec

        self.current_time_label.config(text=self.format_time(current_sec))
        self.remaining_time_label.config(text="-" + self.format_time(remain_sec))

        # Продолжаем цикл
        self.update_handle = self.root.after(100, self.update_scale_position)

    def format_time(self, sec):
        """Преобразует число секунд в M:SS."""
        m = int(sec // 60)
        s = int(sec % 60)
        return f"{m}:{s:02d}"

    # ===== Обработка событий для "живого" перетаскивания ползунка позиции =====
    def _on_scale_press(self, event):
        """
        When the user first clicks on the progress bar, if we are playing, pause.
        Then compute the new position from the click.
        """
        self.is_dragging = True

        # If currently playing, pause
        if self.is_playing and not self.is_paused and self.play_obj:
            self._pause_playback()

        # Figure out where the user clicked
        scale_length = self.position_scale.winfo_width()
        click_x = event.x
        if click_x < 0:
            click_x = 0
        elif click_x > scale_length:
            click_x = scale_length

        fraction = click_x / scale_length
        new_val = fraction * 100
        self.position_var.set(new_val)

        if self.data is not None:
            self.current_frame = int((new_val / 100.0) * len(self.data))
    def _on_scale_drag(self, event):
        """
        While the user drags the slider (B1-Motion), update current_frame
        accordingly. We are in "paused" mode while dragging.
        """
        if self.data is None:
            return
        percent = self.position_var.get()
        self.current_frame = int((percent / 100.0) * len(self.data))

    def _on_scale_release(self, event):
        """
        When the user releases the mouse, if we have data, resume playback
        from the new current_frame if we were playing before.
        """
        self.is_dragging = False
        # If we have data, resume
        if self.data is not None and self.is_paused:
            self._resume_playback()


    # ===== Обработка изменения громкости через ползунок =====
    def _on_volume_change(self, event):
        """
        Change volume on the fly. If we are playing, stop and resume with new volume.
        """
        if self.is_playing and not self.is_paused and self.play_obj:
            # Stop playback
            self.play_obj.stop()
            self.play_obj = None
            self.is_playing = False
            # Now resume from current_frame with new volume
            self._resume_playback()



    # ==================== Кнопка Real-time ====================
    def toggle_realtime(self):
        self.show_realtime_info()

    def show_realtime_info(self):
        dialog = tk.Toplevel(self.root)
        dialog.withdraw()  # Скрываем окно сразу после создания
        dialog.title("Real-time Visualization")

        # Устанавливаем ту же иконку, если она сохранена
        if hasattr(self, "icon_path"):
            dialog.iconbitmap(self.icon_path)

        # Запретить изменение размеров
        dialog.resizable(False, False)

        # Сделать окно модальным
        dialog.transient(self.root)
        dialog.grab_set()

        win_w = 300
        win_h = 120
        dialog.geometry(f"{win_w}x{win_h}")
        dialog.update_idletasks()
        screen_w = dialog.winfo_screenwidth()
        screen_h = dialog.winfo_screenheight()
        x = (screen_w // 2) - (win_w // 2)
        y = (screen_h // 2) - (win_h // 2)
        dialog.geometry(f"{win_w}x{win_h}+{x}+{y}")

        # Теперь показываем окно, когда всё настроено
        dialog.deiconify()

        msg = tk.Label(dialog, text="Real-time visualization will be added\nin future versions!\nStay tuned!❤️.",
                       font=("Arial", 10))
        msg.pack(pady=10)

        def on_ok():
            dialog.destroy()
            self.realtime_mode = not self.realtime_mode
            if self.realtime_mode:
                self.realtime_button.config(text="Real-time ON")
                self.style.configure("RealTime.TButton", foreground="green")
            else:
                self.realtime_button.config(text="Real-time OFF")
                self.style.configure("RealTime.TButton", foreground="red")

        ok_button = ttk.Button(dialog, text="OK", command=on_ok)
        ok_button.pack(pady=5)

    # ----------------- Методы анимации загрузки -----------------
    def show_loading_dialog(self):
        self.loading_dialog = tk.Toplevel(self.root)
        self.loading_dialog.overrideredirect(True)
        self.loading_dialog.configure(bg="black")
        self.loading_dialog.attributes("-topmost", True)
        gif_path = self.resource_path("loading.gif")
        if os.path.exists(gif_path):
            try:
                self.loading_gif = Image.open(gif_path)
                orig_size = self.loading_gif.size
                self.loading_frames = []
                try:
                    while True:
                        frame = self.loading_gif.copy()
                        self.loading_frames.append(ImageTk.PhotoImage(frame))
                        self.loading_gif.seek(len(self.loading_frames))
                except EOFError:
                    pass
                if self.loading_frames:
                    self.loading_frame_index = 0
                    width, height = orig_size
                    screen_width = self.root.winfo_screenwidth()
                    screen_height = self.root.winfo_screenheight()
                    x = (screen_width // 2) - (width // 2)
                    y = (screen_height // 2) - (height // 2)
                    self.loading_dialog.geometry(f"{width}x{height}+{x}+{y}")
                    self.loading_dialog.wm_attributes("-transparentcolor", "black")
                    self.loading_label = tk.Label(self.loading_dialog, bg="black")
                    self.loading_label.pack(expand=True)
                    self.animate_loading_gif()
                else:
                    raise Exception("No frames found in GIF")
            except Exception as e:
                print("Error loading GIF:", e)
                self.loading_label = tk.Label(self.loading_dialog, text="Loading...", fg="lime", bg="black", font=("Courier", 14))
                self.loading_label.pack(expand=True)
        else:
            print("loading.gif not found, using fallback text.")
            self.loading_label = tk.Label(self.loading_dialog, text="Loading...", fg="lime", bg="black", font=("Courier", 14))
            self.loading_label.pack(expand=True)

    def animate_loading_gif(self):
        if self.loading_dialog is None or not self.loading_frames:
            return
        frame = self.loading_frames[self.loading_frame_index]
        self.loading_label.configure(image=frame)
        self.loading_label.image = frame
        self.loading_frame_index = (self.loading_frame_index + 1) % len(self.loading_frames)
        self.loading_dialog.after(100, self.animate_loading_gif)

    def hide_loading_dialog(self):
        if self.loading_dialog is not None:
            self.loading_dialog.destroy()
            self.loading_dialog = None

    # ----------------- Вспомогательные методы -----------------
    def resource_path(self, relative_path):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)

    def show_about(self):
        about_text = (
            "Sound Analyzer 0.3\n"
            "\nVisualize and analyze your audio files with ease!\n\n"
            "Supported Formats:\n"
            "WAV, MP3, FLAC, OGG, AIFF, M4A\n\n"
            "Features:\n"
            "  • Display Waveforms\n"
            "  • Generate Spectrograms (2D & 3D)\n"
            "  • Compute DFT Spectrum\n"
            "  • Playback & volume controls\n"
            "  • More cool stuff to be released soon!\n\n"
            "Voroshka software, 2025\n"
            "Alexey Voronin\n"
            "avoronin3@gatech.edu\n"
            "|     .-.\n"
            "|    /   \\         .-.\n"
            "|   /     \\       /   \\       .-.     .-.     _   _\n"
            "+--/-------\\-----/-----\\-----/---\\---/---\\---/-\\-/-\\/\\/---\n"
            "| /         \\   /       \\   /     '-'     '-'\n"
            "|/           '-'         '-'\n"

        )

        dialog = tk.Toplevel(self.root)
        dialog.withdraw()  # Скрываем окно сразу после создания
        dialog.title("About")

        # Устанавливаем ту же иконку, если она сохранена
        if hasattr(self, "icon_path"):
            dialog.iconbitmap(self.icon_path)

        # Делаем окно модальным
        dialog.transient(self.root)
        dialog.grab_set()

        # Создаём виджеты (Label, кнопка OK)
        text_label = tk.Label(dialog, text=about_text, font=("Arial", 10), justify="left")
        text_label.pack(padx=10, pady=10, fill="both", expand=True)

        ok_button = ttk.Button(dialog, text="OK", command=dialog.destroy)
        ok_button.pack(pady=5)

        # Обновляем геометрию (виджеты должны успеть «разместиться»)
        dialog.update_idletasks()

        # Вычисляем «желаемые» размеры окна
        w = dialog.winfo_reqwidth()
        h = dialog.winfo_reqheight()

        # Позиционируем по центру экрана
        screen_w = dialog.winfo_screenwidth()
        screen_h = dialog.winfo_screenheight()
        x = (screen_w // 2) - (w // 2)
        y = (screen_h // 2) - (h // 2)
        dialog.geometry(f"{w}x{h}+{x}+{y}")

        # Теперь показываем окно
        dialog.deiconify()

        # Запрещаем изменение размеров (только после того, как окно «деиконифицировано»)
        dialog.resizable(False, False)

        # Ожидаем закрытия окна
        self.root.wait_window(dialog)

    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[
            ("Audio Files", "*.wav;*.mp3;*.flac;*.ogg;*.aiff;*.aif;*.m4a"),
            ("WAV Files", "*.wav"),
            ("MP3 Files", "*.mp3"),
            ("FLAC Files", "*.flac"),
            ("OGG Files", "*.ogg"),
            ("AIFF Files", "*.aiff;*.aif"),
            ("M4A Files", "*.m4a"),
            ("All Files", "*.*")
        ])
        if file_path:
            self.analyze_audio(file_path)

    def check_data(self):
        if self.data is None:
            messagebox.showerror("Error", "Please load an audio file first!")
            return False
        return True

    def get_bit_depth(self, file_path, ext):
        try:
            if ext == "wav":
                with wave.open(file_path, 'rb') as wav_file:
                    return f"{wav_file.getsampwidth() * 8}-bit"
            else:
                info = sf.info(file_path)
                if "PCM" in info.subtype:
                    return f"{info.subtype.replace('PCM_', '')}-bit"
                else:
                    return "n/a"
        except Exception:
            return "n/a"

    def analyze_audio(self, file_path):
        self.on_stop()
        try:
            file_name = os.path.basename(file_path)
            ext = os.path.splitext(file_path)[1].lower().replace('.', '')
            file_format = ext.upper()
            bit_depth = self.get_bit_depth(file_path, ext)

            if ext in ["wav", "flac", "ogg", "aiff", "aif"]:
                try:
                    sample_rate, data = wavfile.read(file_path)
                    data = data.astype(np.float32)
                    max_abs = np.max(np.abs(data))
                    if max_abs > 0:
                        data /= max_abs
                except Exception:
                    data, sample_rate = sf.read(file_path, always_2d=True)
                if data.ndim > 1:
                    channels = data.shape[1]
                    if channels == 1:
                        data = data[:, 0]
                else:
                    channels = 1
            else:
                # Для mp3, m4a и т.д.
                audio = AudioSegment.from_file(file_path)
                sample_rate = audio.frame_rate
                channels = audio.channels
                data = np.array(audio.get_array_of_samples())
                if channels > 1:
                    data = data.reshape((-1, channels))
                max_val = float(2 ** (8 * audio.sample_width))
                data = data.astype(np.float32) / max_val

            self.data = data
            self.sample_rate = sample_rate

            # === Изменение: дополнительно храним audio_segment для воспроизведения
            self.audio_segment = AudioSegment.from_file(file_path)

            # Статистика
            if channels == 1:
                min_val = np.min(data)
                max_val = np.max(data)
                mean_val = np.mean(data)
                rms_val = np.sqrt(np.mean(data ** 2))
                channel_info = "Mono"
                stats_str = (
                    f"🔎Min: {min_val:.4f}\n"
                    f"🔎Max: {max_val:.4f}\n"
                    f"📉Mean: {mean_val:.4f}, RMS: {rms_val:.4f}"
                )
            else:
                channel_info = "Stereo" if channels == 2 else f"{channels} channels"
                min_val = np.min(data, axis=0)
                max_val = np.max(data, axis=0)
                mean_val = np.mean(data, axis=0)
                rms_val = np.sqrt(np.mean(data ** 2, axis=0))
                stats_list = []
                for i in range(channels):
                    stats_list.append(
                        f"Channel {i + 1}:\n"
                        f"  🔎Min: {min_val[i]:.4f}, Max: {max_val[i]:.4f}\n"
                        f"  📉Mean: {mean_val[i]:.4f}, RMS: {rms_val[i]:.4f}"
                    )
                stats_str = "\n".join(stats_list)

            self.file_label.config(text="File loaded!")
            self.info_label.config(
                text=(
                    f"📂 {file_name}\n"
                    f"📄 Format: {file_format}\n"
                    f"🎵Sample rate: {sample_rate} Hz\n"
                    f"📝Bit depth: {bit_depth}\n"
                    f"⌛Duration: {len(data) / sample_rate:.2f} sec\n"
                    f"🔊Channels: {channel_info}\n"
                    f"{stats_str}"
                )
            )
            for button in self.buttons.values():
                button.config(state="normal")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to process the file!\n{str(e)}")

    # ----------------- Методы построения графиков (Waveform, Spectrogram, ...) -----------------
    def show_waveform(self):
        if not self.check_data():
            return
        self.show_loading_dialog()
        self.root.after(1500, self._plot_waveform)

    def _plot_waveform(self):
        # Если placeholder_label отображается, скрываем его и создаем Figure, Canvas, Toolbar
        if self.placeholder_label is not None and self.placeholder_label.winfo_ismapped():
            self.placeholder_label.pack_forget()
            self.placeholder_label = None

            self.figure = Figure(figsize=(6, 4), dpi=100)
            self.canvas = FigureCanvasTkAgg(self.figure, master=self.right_frame)
            self.canvas_widget = self.canvas.get_tk_widget()
            self.canvas_widget.pack(fill="both", expand=True)

            self.toolbar = NavigationToolbar2Tk(self.canvas, self.right_frame)
            self.toolbar.update()
            self.toolbar.pack(side="bottom", fill="x")

        self.figure.clear()
        if self.data.ndim == 1:
            ax = self.figure.add_subplot(111)
            time = np.linspace(0, len(self.data) / self.sample_rate, num=len(self.data))
            ax.plot(time, self.data, color='blue')
            ax.set_title("Waveform (Mono)")
            ax.set_xlabel("Time (sec)")
            ax.set_ylabel("Amplitude")
            ax.grid()
        else:
            n_channels = self.data.shape[1]
            if n_channels == 2:
                colors = ['blue', 'red']
            else:
                colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown']
            for i in range(n_channels):
                ax = self.figure.add_subplot(n_channels, 1, i + 1)
                channel_data = self.data[:, i]
                time = np.linspace(0, len(channel_data) / self.sample_rate, num=len(channel_data))
                ax.plot(time, channel_data, color=colors[i % len(colors)])
                ax.set_title(f"Waveform (Channel {i + 1})")
                ax.set_ylabel("Amplitude")
                ax.grid()
                ax.set_xlabel("Time (sec)")
        self.canvas.draw()
        self.hide_loading_dialog()

    def show_spectrogram(self):
            if not self.check_data():
                return
            self.show_loading_dialog()
            self.root.after(1500, self._plot_spectrogram)

    def _plot_spectrogram(self):
        # Если placeholder_label отображается, скрываем его и создаем Figure, Canvas, Toolbar
        if self.placeholder_label is not None and self.placeholder_label.winfo_ismapped():
            self.placeholder_label.pack_forget()
            self.placeholder_label = None

            self.figure = Figure(figsize=(6, 4), dpi=100)
            self.canvas = FigureCanvasTkAgg(self.figure, master=self.right_frame)
            self.canvas_widget = self.canvas.get_tk_widget()
            self.canvas_widget.pack(fill="both", expand=True)

            self.toolbar = NavigationToolbar2Tk(self.canvas, self.right_frame)
            self.toolbar.update()
            self.toolbar.pack(side="bottom", fill="x")

        self.figure.clear()
        if self.data.ndim == 1:
            ax = self.figure.add_subplot(111)
            ax.specgram(self.data, Fs=self.sample_rate, cmap='inferno', NFFT=2048, noverlap=1024)
            ax.set_title("Spectrogram (Mono)")
            ax.set_xlabel("Time (sec)")
            ax.set_ylabel("Frequency (Hz)")
        else:
            n_channels = self.data.shape[1]
            for i in range(n_channels):
                ax = self.figure.add_subplot(n_channels, 1, i + 1)
                channel_data = self.data[:, i]
                ax.specgram(channel_data, Fs=self.sample_rate, cmap='inferno', NFFT=2048, noverlap=1024)
                ax.set_title(f"Spectrogram (Channel {i + 1})")
                ax.set_ylabel("Frequency (Hz)")
            ax.set_xlabel("Time (sec)")
        self.canvas.draw()
        self.hide_loading_dialog()

    def show_dft(self):
        if not self.check_data():
            return
        self.show_loading_dialog()
        self.root.after(1500, self._plot_dft)

    def _plot_dft(self):
        # Если placeholder_label отображается, скрываем его и создаем Figure, Canvas, Toolbar
        if self.placeholder_label is not None and self.placeholder_label.winfo_ismapped():
            self.placeholder_label.pack_forget()
            self.placeholder_label = None

            self.figure = Figure(figsize=(6, 4), dpi=100)
            self.canvas = FigureCanvasTkAgg(self.figure, master=self.right_frame)
            self.canvas_widget = self.canvas.get_tk_widget()
            self.canvas_widget.pack(fill="both", expand=True)

            self.toolbar = NavigationToolbar2Tk(self.canvas, self.right_frame)
            self.toolbar.update()
            self.toolbar.pack(side="bottom", fill="x")

        self.figure.clear()
        if self.data.ndim == 1:
            ax = self.figure.add_subplot(111)
            d = self.data
            spectrum = np.fft.fft(d)
            freqs = np.fft.fftfreq(len(d), d=1 / self.sample_rate)
            half = len(freqs) // 2
            ax.plot(freqs[:half], np.abs(spectrum[:half]), color='purple')
            ax.set_title("DFT Spectrum (Mono)")
            ax.set_xlabel("Frequency (Hz)")
            ax.set_ylabel("Amplitude")
            ax.grid()
        else:
            n_channels = self.data.shape[1]
            for i in range(n_channels):
                ax = self.figure.add_subplot(n_channels, 1, i + 1)
                d = self.data[:, i]
                spectrum = np.fft.fft(d)
                freqs = np.fft.fftfreq(len(d), d=1 / self.sample_rate)
                half = len(freqs) // 2
                ax.plot(freqs[:half], np.abs(spectrum[:half]), color='purple')
                ax.set_title(f"DFT Spectrum (Channel {i + 1})")
                ax.set_ylabel("Amplitude")
                ax.grid()
            ax.set_xlabel("Frequency (Hz)")
        self.canvas.draw()
        self.hide_loading_dialog()

    def show_3d_spectrogram(self):
        if not self.check_data():
            return
        self.show_loading_dialog()
        self.root.after(1500, self._plot_3d_spectrogram)

    def _plot_3d_spectrogram(self):
        from mpl_toolkits.mplot3d import Axes3D  # noqa
        # Если placeholder_label отображается, скрываем его и создаем Figure, Canvas, Toolbar
        if self.placeholder_label is not None and self.placeholder_label.winfo_ismapped():
            self.placeholder_label.pack_forget()
            self.placeholder_label = None

            self.figure = Figure(figsize=(6, 4), dpi=100)
            self.canvas = FigureCanvasTkAgg(self.figure, master=self.right_frame)
            self.canvas_widget = self.canvas.get_tk_widget()
            self.canvas_widget.pack(fill="both", expand=True)

            self.toolbar = NavigationToolbar2Tk(self.canvas, self.right_frame)
            self.toolbar.update()
            self.toolbar.pack(side="bottom", fill="x")

        self.figure.clear()
        if self.data.ndim == 1:
            ax = self.figure.add_subplot(111, projection='3d')
            nperseg = min(2048, len(self.data) // 10)
            f, t, Sxx = spectrogram(self.data, self.sample_rate, nperseg=nperseg)
            T, F = np.meshgrid(t, f)
            ax.plot_surface(T, F, 10 * np.log10(Sxx + 1e-10), cmap="jet")
            ax.set_title("3D Spectrogram (Mono)")
            ax.set_xlabel("Time (sec)")
            ax.set_ylabel("Frequency (Hz)")
            ax.set_zlabel("Magnitude (dB)")
        else:
            n_channels = self.data.shape[1]
            nperseg = min(2048, self.data.shape[0] // 10)
            for i in range(n_channels):
                ax = self.figure.add_subplot(1, n_channels, i + 1, projection='3d')
                f, t, Sxx = spectrogram(self.data[:, i], self.sample_rate, nperseg=nperseg)
                T, F = np.meshgrid(t, f)
                ax.plot_surface(T, F, 10 * np.log10(Sxx + 1e-10), cmap="jet")
                ax.set_title(f"3D Spectrogram (Channel {i + 1})")
                ax.set_ylabel("Frequency (Hz)")
                ax.set_zlabel("Magnitude (dB)")
            ax.set_xlabel("Time (sec)")
        self.canvas.draw()
        self.hide_loading_dialog()


# ---------------------- Splash Screen ----------------------
def show_splash(root, duration=4000):
    splash = tk.Toplevel(root)
    splash.overrideredirect(True)
    splash.config(bg="#F5F5F5")
    logo_path = os.path.join(sys._MEIPASS, "logo.png") if hasattr(sys, '_MEIPASS') else os.path.join(os.path.abspath("."), "logo.png")
    if os.path.exists(logo_path):
        splash_image = tk.PhotoImage(file=logo_path).subsample(2, 2)
        splash_label = tk.Label(splash, image=splash_image, bg="#F5F5F5")
        splash_label.image = splash_image
        splash_label.pack()
    else:
        splash_label = tk.Label(splash, text="Sound File Analyzer", font=("Arial", 24), bg="#F5F5F5")
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


# ---------------------- Основной блок ----------------------
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Скрываем главное окно
    show_splash(root, duration=2000)  # Splash screen на 2 секунды
    root.after(2000, root.deiconify)  # После 2 секунд показываем главное окно
    app = SoundAnalyzer(root)
    root.mainloop()