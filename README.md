# Real-Time Driver Drowsiness Detection System

A computer vision-based embedded safety solution designed to prevent road accidents by monitoring driver fatigue in real-time. This system utilizes **Python**, **OpenCV**, and **MediaPipe Face Mesh** to accurately calculate the Eye Aspect Ratio (EAR) and communicate wirelessly with hardware alerts.

## 🚀 Key Features
* **Dual-Eye Monitoring:** Simultaneously tracks and analyzes facial landmarks for both eyes to ensure accuracy.
* **Real-Time EAR Calculation:** Measures eye closure thresholds dynamically.
* **Hardware Integration:** Capable of sending real-time HTTP requests to an **ESP32** microcontroller to trigger physical alarms/buzzers when drowsiness is detected.
* **Lightweight UI:** Built-in graphical interface using **Tkinter** for seamless video streaming.

## 🛠️ Tech Stack & Tools
* **Language:** Python 3.x
* **AI/Computer Vision:** MediaPipe (Face Mesh), OpenCV
* **Data Processing:** NumPy
* **GUI:** Tkinter
* **Networking:** Requests (for ESP32 communication)

## 📂 Project Structure
* `drowsiness_detection.py` - The main Python script handling the computer vision pipeline and hardware triggers.
* `requirements.txt` - File containing the necessary dependencies to replicate the project environment.

## 🔧 How to Run
1. Clone the repository or download the files.
2. Install the dependencies using:
   ```bash
   pip install -r requirements.txt
