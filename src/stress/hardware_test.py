"""
Hardware Test — ECG AD8232 via ESP32 Serial
============================================

Standalone test script to verify ESP32 + AD8232 ECG hardware
is working correctly before using it in the dashboard.

Run with:
    python src/stress/hardware_test.py

Press Ctrl+C to stop.
"""

import sys
import os
import time
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.utils.config import SERIAL_PORT, SERIAL_BAUD_RATE


def test_serial_connection():
    """Test basic serial connection to ESP32."""
    try:
        import serial
    except ImportError:
        print("❌ pyserial not installed!")
        print("   Run: pip install pyserial")
        return False

    print(f"Connecting to {SERIAL_PORT} at {SERIAL_BAUD_RATE} baud...")

    try:
        ser = serial.Serial(SERIAL_PORT, SERIAL_BAUD_RATE, timeout=3)
        print(f"✅ Connected to {SERIAL_PORT}")
        time.sleep(2)  # Wait for ESP32 boot
        return ser
    except Exception as e:
        print(f"❌ Cannot connect: {e}")
        print("\n   Possible fixes:")
        print("   1. Close Arduino Serial Monitor (only one app can use the port)")
        print("   2. Check USB cable is connected")
        print(f"   3. Verify port is {SERIAL_PORT} in Device Manager")
        return None


def run_hardware_test():
    """Run live ECG data test."""
    print("=" * 60)
    print("  PTSD Trigger Detection — ECG Hardware Test")
    print("  ESP32 + AD8232 ECG Sensor")
    print("=" * 60)
    print()

    ser = test_serial_connection()
    if not ser:
        return

    print()
    print("Reading ECG data... (Press Ctrl+C to stop)")
    print("-" * 60)
    print(f"  {'Time':>8}  {'HR (bpm)':>10}  {'HRV (ms)':>10}  {'ECG Raw':>10}  {'Status'}")
    print("-" * 60)

    readings = 0
    valid_readings = 0
    hr_values = []

    try:
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode("utf-8").strip()

                if not line or not line.startswith("{"):
                    continue

                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue

                readings += 1
                hr = data.get("heart_rate", 0)
                hrv = data.get("hrv", 0)
                ecg_raw = data.get("ecg_raw", 0)
                leads_off = data.get("leads_off", True)

                now = time.strftime("%H:%M:%S")

                if leads_off:
                    status = "⚠️  LEADS OFF — attach electrodes"
                    print(f"  {now:>8}  {'---':>10}  {'---':>10}  {'---':>10}  {status}")
                elif hr == 0:
                    status = "⏳ Calibrating..."
                    print(f"  {now:>8}  {'...':>10}  {'...':>10}  {ecg_raw:>10}  {status}")
                else:
                    valid_readings += 1
                    hr_values.append(hr)

                    # Color indicator
                    if hr < 60:
                        indicator = "🔵"  # Low
                    elif hr < 100:
                        indicator = "🟢"  # Normal
                    elif hr < 130:
                        indicator = "🟡"  # Elevated
                    else:
                        indicator = "🔴"  # High

                    status = f"{indicator} {'Normal' if 60 <= hr <= 100 else 'Elevated' if hr > 100 else 'Low'}"
                    print(f"  {now:>8}  {hr:>10.1f}  {hrv:>10.1f}  {ecg_raw:>10}  {status}")

            time.sleep(0.1)

    except KeyboardInterrupt:
        print()
        print("=" * 60)
        print("  Test Summary")
        print("=" * 60)
        print(f"  Total readings:   {readings}")
        print(f"  Valid readings:   {valid_readings}")
        if hr_values:
            avg_hr = sum(hr_values) / len(hr_values)
            min_hr = min(hr_values)
            max_hr = max(hr_values)
            print(f"  Average HR:       {avg_hr:.1f} bpm")
            print(f"  Min HR:           {min_hr:.1f} bpm")
            print(f"  Max HR:           {max_hr:.1f} bpm")

            if 50 <= avg_hr <= 120:
                print(f"\n  ✅ ECG sensor is working correctly!")
                print(f"  ✅ Ready to use with dashboard")
            else:
                print(f"\n  ⚠️  Heart rate seems unusual. Check electrode placement.")
        else:
            print(f"\n  ❌ No valid heart rate readings received.")
            print(f"     Check electrode placement and wiring.")

        print()

    finally:
        ser.close()
        print("  Serial connection closed.")


if __name__ == "__main__":
    run_hardware_test()
