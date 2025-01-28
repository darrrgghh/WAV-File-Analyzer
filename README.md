# 🎵 Spectrum Analyzer

This project is a **spectrum analyzer** that processes `.wav` files and visualizes their frequency spectrum.  
It was developed as part of an attempt to understand **Fast Fourier Transform (FFT)** in detail while taking a **Digital Signal Processing (DSP)** course.

## 🚀 Features
- Uses **NumPy**, **SciPy**, and **Matplotlib** to process and visualize audio signals.
- Supports `.wav` file input.
- Implements both:
  - **Fast Fourier Transform (FFT)** for frequency domain analysis.
  - **Discrete Fourier Transform (DFT)** manually for educational purposes.
- Displays **two visualizations**:
  - **2D Spectrum** (FFT or DFT result)
  - **3D Spectrogram** (frequency changes over time)
- Includes `wav.py`, which **prints digital values** from the `.wav` file.

## 📂 Installation
1. **Clone the repository**:
   ```bash
   git clone https://github.com/darrrgghh/Spectrum-Analyzer.git
   cd Spectrum-Analyzer
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
1. Place  a `````.wav````` file in the project folder.
2. Run the spectrum analyzer script:
```bash
python Spectrum_Analyzer.py
```
- The program will display:
  ### 1️⃣ 2D Spectrum Graph (FFT or DFT Result)
- **Shows the amplitude of different frequencies** in the `.wav` file.
- **X-axis** → Frequency (Hz)
- **Y-axis** → Amplitude
- This represents a **single snapshot** of the frequency content of the audio file.

  ### 2️⃣ 3D Spectrogram (Frequency over Time)
- **Shows how the frequency content changes over time** in the audio.
- **X-axis** → Frequency (Hz)
- **Y-axis** → Time (seconds)
- **Z-axis (color)** → Magnitude (dB)
- This provides a **time-frequency representation** of the signal, making it easier to analyze changes in tone.

3. To display raw audio samples as numbers, run:

```bash
python wav.py
```
This script prints **digital values** of the `.wav` file, including:

- **The sampling rate** (`fs`) in Hz (e.g., `44100 Hz` or `48000 Hz`).
- **The first N samples** of the waveform (adjustable).



## 🛠 Future Improvements
- Add real-time audio analysis
- Implement GUI
- Expand support for more audio formats
## 📜 License
This project is licensed under the MIT License.