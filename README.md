# 🎵 WAV File Analyzer

This project is a **WAV file analyzer** that processes `.wav` files and provides detailed visualizations of their frequency spectrum and waveform characteristics. It was developed as part of a **Digital Signal Processing (DSP)** course at Georgia Tech, with the goal of gaining a deeper understanding of **Fourier Transform** concepts, including the **Fast Fourier Transform (FFT)** and the **Discrete Fourier Transform (DFT)**.

The analyzer is designed to help users explore audio signals in both the **time domain** (waveform) and the **frequency domain** (spectrum). It provides a user-friendly interface for loading `.wav` files, analyzing their properties, and visualizing the data in various ways, including **waveforms**, **spectrograms**, and **3D spectrograms**.

Whether you're a student learning about DSP, a musician analyzing audio files, or just someone curious about sound, this tool offers an intuitive way to explore the intricacies of audio signals.

## 🚀 Features
- Uses **NumPy**, **SciPy**, and **Matplotlib** to process and visualize audio signals.
- Supports `.wav` file input.
- Implements both:
  - **Fast Fourier Transform (FFT)** for frequency domain analysis.
  - **Discrete Fourier Transform (DFT)** manually for educational purposes.
- Displays **multiple visualizations**:
  - **Waveform** (amplitude over time)
  - **Spectrogram** (frequency changes over time)
  - **DFT Spectrum** (frequency domain representation)
  - **3D Spectrogram** (frequency changes over time in 3D)
- Includes a **GUI** built with **Tkinter** for easy file selection and visualization.

## 📂 Installation
1. **Clone the repository**:
   ```bash
   git clone https://github.com/darrrgghh/WAV-File-Analyzer.git
   cd WAV-File-Analyzer
2. **Create and activate virtual environment**:
- For Windows:
```powershell
python -m venv .venv
.\.venv\Scripts\activate
```
- For MacOS/ Linux:
```bash
python -m venv .venv
source .venv/bin/activate
```
 Install dependencies:
 ```bash
pip install -r requirements.txt
```
## 🎛 How to use
1. Run the wav file analyzer script:
```bash
python wav_analyzer.py
```
2. **Select a ```.wav``` file** using the file dialog.
3.  The program will display the following information about the audio file:
- **File path**
- **Number of channels**
- **Sample rate**
- **Bit depth**
- **Duration**
- **Min, Max, Mean, and RMS values** of the audio signal
4. **Visualize the audio data** using the provided buttons:
- **Show Waveform**: Displays the amplitude of the audio signal over time.
- **Show Spectrogram**: Displays a 2D spectrogram showing frequency content over time.
- **Show DFT Spectrum**: Displays the frequency spectrum computed using the Discrete Fourier Transform.
- **Show 3D Spectrogram**: Displays a 3D spectrogram showing frequency content over time.
## 🛠 Future Improvements
- Add real-time audio analysis
- Improve the GUI with more customization options.
- Expand support for more audio formats (e.g., MP3, FLAC).
- Add export functionality for visualizations.
## 📜 License
This project is licensed under the MIT License.