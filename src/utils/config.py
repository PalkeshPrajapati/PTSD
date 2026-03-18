"""
Global Configuration for PTSD Trigger Detection System
All settings in one place — easy to change behavior without touching code.
"""

import os

# ============================================================
# PATHS
# ============================================================
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")

# ============================================================
# HEART RATE DATA SOURCE
# Switch between dummy (simulated) and real hardware sensor
# Options: "DUMMY" or "SERIAL"
# ============================================================
HEART_RATE_SOURCE = "DUMMY"

# Serial port settings (used when HEART_RATE_SOURCE = "SERIAL")
SERIAL_PORT = "COM3"  # Change to your ESP32 port
SERIAL_BAUD_RATE = 115200

# ============================================================
# EMOTION DETECTION (DeepFace)
# ============================================================
EMOTION_MODEL = "VGG-Face"  # Options: VGG-Face, Facenet, OpenFace, DeepFace, ArcFace
EMOTION_DETECTOR_BACKEND = "opencv"  # Options: opencv, ssd, mtcnn, retinaface
EMOTION_CONFIDENCE_THRESHOLD = 0.3  # Minimum confidence to report emotion

# PTSD-relevant emotions (these contribute to risk score)
TRIGGER_EMOTIONS = ["fear", "angry", "sad", "disgust"]
SAFE_EMOTIONS = ["happy", "neutral", "surprise"]

# ============================================================
# OBJECT DETECTION (YOLO26 — Latest Ultralytics, Jan 2026)
# ============================================================
YOLO_MODEL = "yolo26n.pt"  # YOLO26 nano — smaller, faster, more accurate than YOLOv8
YOLO_CONFIDENCE_THRESHOLD = 0.5

# Objects that may trigger PTSD (COCO class names)
TRIGGER_OBJECTS = [
    "knife", "scissors",  # Sharp objects
    "car", "truck", "bus",  # Vehicles (accident triggers)
    "person",  # Crowd detection (multiple persons)
    "fire hydrant",  # Emergency associations
]

# Crowd detection: if more than this many people → crowd trigger
CROWD_THRESHOLD = 5

# ============================================================
# AUDIO CLASSIFICATION (YAMNet)
# ============================================================
YAMNET_CONFIDENCE_THRESHOLD = 0.3

# Sound categories that may trigger PTSD (YAMNet class names)
TRIGGER_SOUNDS = [
    "Gunshot, gunfire",
    "Explosion",
    "Siren",
    "Screaming",
    "Shout",
    "Glass breaking",
    "Thunder",
    "Alarm",
    "Car alarm",
    "Emergency vehicle",
    "Fire alarm",
    "Crying, sobbing",
]

# Audio recording settings
AUDIO_SAMPLE_RATE = 16000  # YAMNet expects 16kHz
AUDIO_DURATION = 1.0  # Seconds of audio per classification

# ============================================================
# STRESS / HEART RATE
# ============================================================
# Normal resting heart rate range (bpm)
NORMAL_HR_MIN = 60
NORMAL_HR_MAX = 100

# Stress thresholds
STRESS_HR_THRESHOLD = 100  # HR above this = stress indicator
STRESS_HR_CRITICAL = 130   # HR above this = high stress

# ============================================================
# RISK FUSION
# ============================================================
# Weights for each module in the final risk score
FUSION_WEIGHTS = {
    "emotion": 0.30,   # 30% weight
    "object": 0.20,    # 20% weight
    "audio": 0.25,     # 25% weight
    "stress": 0.25,    # 25% weight
}

# Risk levels
RISK_LOW = 30       # 0-30% = Low risk
RISK_MEDIUM = 60    # 31-60% = Medium risk
RISK_HIGH = 100     # 61-100% = High risk

# ============================================================
# DASHBOARD
# ============================================================
DASHBOARD_REFRESH_RATE = 2  # Seconds between dashboard updates
MAX_HISTORY_ITEMS = 100     # Max trigger events to keep in memory
