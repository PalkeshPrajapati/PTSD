"""
Serial Sensor Reader for PTSD Trigger Detection System

Reads real physiological data from hardware sensors via serial port.
Hardware: MAX30102 pulse sensor + ESP32 microcontroller

This module is activated when config.py HEART_RATE_SOURCE = "SERIAL"
Until hardware is connected, use dummy_data.py instead.

Expected serial data format from ESP32 (JSON):
    {"heart_rate": 75.2, "gsr": 3.5, "hrv": 55.0, "skin_temp": 34.1}
"""

import sys
import os
import time
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.utils.config import SERIAL_PORT, SERIAL_BAUD_RATE
from src.utils.logger import setup_logger

logger = setup_logger("SerialReader")


class SerialSensorStream:
    """
    Reads physiological sensor data from ESP32 via serial port.
    Drop-in replacement for DummySensorStream.
    """

    def __init__(self):
        """Initialize serial connection to ESP32."""
        self.port = SERIAL_PORT
        self.baud_rate = SERIAL_BAUD_RATE
        self.serial_conn = None
        self.current_state = "unknown"  # State comes from sensor data

        try:
            import serial
            self.serial_conn = serial.Serial(self.port, self.baud_rate, timeout=2)
            logger.info(f"Connected to {self.port} at {self.baud_rate} baud")
            time.sleep(2)  # Wait for ESP32 to initialize
        except ImportError:
            logger.error("pyserial not installed! Run: pip install pyserial")
        except Exception as e:
            logger.error(f"Cannot connect to {self.port}: {e}")
            logger.info("Falling back to dummy data. Check your ESP32 connection.")

    def get_reading(self) -> dict:
        """
        Read one sensor measurement from serial.

        Returns:
            dict with heart_rate, gsr, hrv, skin_temp, timestamp
        """
        if self.serial_conn is None or not self.serial_conn.is_open:
            logger.warning("Serial not connected, returning default values")
            return {
                "heart_rate": 70.0,
                "gsr": 3.0,
                "hrv": 50.0,
                "skin_temp": 34.0,
                "state": "unknown",
                "timestamp": time.time(),
            }

        try:
            line = self.serial_conn.readline().decode("utf-8").strip()
            if line:
                data = json.loads(line)
                data["timestamp"] = time.time()
                data["state"] = self._classify_state(data)
                return data
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.debug(f"Serial parse error: {e}")
        except Exception as e:
            logger.error(f"Serial read error: {e}")

        return {
            "heart_rate": 70.0,
            "gsr": 3.0,
            "hrv": 50.0,
            "skin_temp": 34.0,
            "state": "unknown",
            "timestamp": time.time(),
        }

    def _classify_state(self, data: dict) -> str:
        """Quick classification of state from raw values."""
        hr = data.get("heart_rate", 70)
        if hr > 110:
            return "high_stress"
        elif hr > 85:
            return "mild_stress"
        return "calm"

    def set_state(self, state: str):
        """No-op for real hardware (state comes from sensors)."""
        pass

    def close(self):
        """Close serial connection."""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            logger.info("Serial connection closed")
