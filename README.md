# 🎵 Spectrum Analyzer

This project is a **spectrum analyzer** that processes `.wav` files and visualizes their frequency spectrum.  
It was developed as part of an attempt to understand **Fast Fourier Transform (FFT)** in detail while taking a **Digital Signal Processing (DSP)** course.

## 🚀 Features
- Uses **NumPy**, **SciPy**, and **Matplotlib** to process and visualize audio signals.
- Supports `.wav` file input.
- Implements **Fast Fourier Transform (FFT)** for frequency domain analysis.

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
2. Run the script
```bash
python Spectrum_Analyzer.py
```
3. The program will display the **frequency spectrum** of the input audio.

## 🛠 Future Improvements
- Add real-time audio analysis
- Implement GUI
- Expand support for more audio formats
## 📜 License
This project is licensed under the MIT License.