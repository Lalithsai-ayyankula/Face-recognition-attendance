# Face Recognition Attendance System

A web-based attendance management system built with Python, Flask, OpenCV, and face recognition. The application allows users to log in by branch and role, register faces for recognition, and automatically mark attendance through a real-time video stream.

## Project Overview

This project is designed for educational institutions to streamline attendance tracking using facial recognition technology. It provides:

- Role-based authentication for students, teachers, and class representatives
- Real-time face recognition from a webcam
- Attendance logging for recognized individuals
- Branch-wise organization and management
- Admin and student dashboards

## Features

- Secure login with branch and user-based authentication
- Student, teacher, and CR role support
- Live camera feed with face recognition overlays
- Attendance tracking and record viewing
- Face registration by uploading multiple images
- Branch-specific data and attendance storage

## Tech Stack

- Python 3.x
- Flask
- OpenCV
- face-recognition
- Flask-Session
- Pandas
- PyMongo
- NumPy
- Pillow
- scikit-learn

## Project Structure

```text
.
├── app.py
├── attendance_manager.py
├── auth.py
├── config.py
├── database.py
├── face_recognition_service.py
├── train_model.py
├── requirements.txt
├── static/
├── templates/
├── data/
└── README.md
```

## Prerequisites

Before running the application, make sure you have:

- Python 3.8 or later installed
- A working webcam connected to your device
- MongoDB running locally or configured properly

## Installation

1. Clone the repository:

```bash
git clone https://github.com/Lalithsai-ayyankula/Face-recognition-attendance.git
cd Face-recognition-attendance
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate         # Windows
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Update the configuration values in the application settings file if needed, especially database and application settings.

## Running the Application

Start the Flask server:

```bash
python app.py
```

Then open your browser and go to:

```text
http://127.0.0.1:5000
```

## Usage

1. Open the application in your browser.
2. Log in using the available branch and role credentials.
3. Use the webcam-based recognition flow to mark attendance.
4. Register new members by uploading facial images.
5. View attendance records through the dashboard.

## Notes

- Ensure your camera is accessible when running face recognition.
- Face encoding data is stored and loaded from the branch-specific data directory.
- The application uses role-based permissions for access control.

## License

This project is open-source and available for educational and development purposes.

## Contact

For questions or support, please reach out through the project repository.
