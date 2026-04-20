/*
 * PTSD Trigger Detection System — ESP32 + AD8232 ECG
 * VERSION 2: Improved R-peak detection with noise filtering
 * 
 * Wiring:
 *   AD8232 GND    → ESP32 GND
 *   AD8232 3.3V   → ESP32 3V3
 *   AD8232 OUTPUT → ESP32 D34
 *   AD8232 LO-    → ESP32 D18
 *   AD8232 LO+    → ESP32 D19
 */

#define ECG_PIN    34
#define LO_MINUS   18
#define LO_PLUS    19

// ── Moving Average Filter (smooths noisy ECG signal) ──
#define FILTER_SIZE 10
int filterBuf[FILTER_SIZE];
int filterIndex = 0;
long filterSum = 0;
bool filterFull = false;

// ── R-Peak Detection ──
float heartRate = 0.0;
float hrv = 0.0;
float smoothedHR = 0.0;
bool hrValid = false;

unsigned long lastPeakTime = 0;
unsigned long rrIntervals[10];
int rrIndex = 0;
int rrCount = 0;

// Adaptive threshold
float baseline = 2048.0;   // Running baseline
float peakLevel = 2200.0;  // Running peak level
int threshold = 2500;

// Timing
unsigned long lastSendTime = 0;
const int SEND_INTERVAL = 1000;

// ── Smoothing Filter ──
int applyFilter(int rawValue) {
  filterSum -= filterBuf[filterIndex];
  filterBuf[filterIndex] = rawValue;
  filterSum += rawValue;
  filterIndex = (filterIndex + 1) % FILTER_SIZE;
  if (filterIndex == 0) filterFull = true;
  
  int count = filterFull ? FILTER_SIZE : filterIndex;
  if (count == 0) return rawValue;
  return filterSum / count;
}

void setup() {
  Serial.begin(115200);
  
  pinMode(LO_MINUS, INPUT);
  pinMode(LO_PLUS, INPUT);
  
  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);
  
  // Initialize filter buffer
  for (int i = 0; i < FILTER_SIZE; i++) filterBuf[i] = 2048;
  filterSum = 2048 * FILTER_SIZE;
  
  delay(1000);
  Serial.println("{\"status\":\"ESP32 ECG v2 Ready\"}");
}

void loop() {
  bool leadsOff = digitalRead(LO_MINUS) == HIGH || digitalRead(LO_PLUS) == HIGH;
  
  if (!leadsOff) {
    int rawEcg = analogRead(ECG_PIN);
    int filtered = applyFilter(rawEcg);
    
    // Update running baseline (slow adaptation)
    baseline = baseline * 0.999 + filtered * 0.001;
    
    // Update peak level (faster adaptation)
    if (filtered > peakLevel) {
      peakLevel = peakLevel * 0.95 + filtered * 0.05;
    } else {
      peakLevel = peakLevel * 0.999 + filtered * 0.001;
    }
    
    // Threshold = midpoint between baseline and peak
    float range = peakLevel - baseline;
    threshold = baseline + range * 0.6;
    
    // Only try to detect peaks if signal has enough range (>200 ADC units)
    if (range > 200) {
      detectRPeak(filtered);
    }
  } else {
    // Reset when electrodes are off
    hrValid = false;
    smoothedHR = 0;
    rrCount = 0;
  }
  
  if (millis() - lastSendTime >= SEND_INTERVAL) {
    lastSendTime = millis();
    sendData(leadsOff);
  }
  
  delay(5);  // ~200 Hz sampling
}

void detectRPeak(int value) {
  static bool aboveThreshold = false;
  static unsigned long lastDetection = 0;
  static int peakValue = 0;
  
  unsigned long now = millis();
  
  // Track peak while above threshold
  if (value > threshold) {
    if (value > peakValue) peakValue = value;
    
    if (!aboveThreshold && (now - lastDetection > 400)) {
      // Minimum 400ms between peaks = max 150 BPM
      aboveThreshold = true;
    }
  }
  
  // When signal drops below threshold, the peak is confirmed
  if (value < threshold && aboveThreshold) {
    aboveThreshold = false;
    lastDetection = now;
    peakValue = 0;
    
    if (lastPeakTime > 0) {
      unsigned long rrInterval = now - lastPeakTime;
      
      // Valid range: 400ms-1500ms (40-150 BPM)
      if (rrInterval >= 400 && rrInterval <= 1500) {
        rrIntervals[rrIndex] = rrInterval;
        rrIndex = (rrIndex + 1) % 10;
        if (rrCount < 10) rrCount++;
        
        float instantHR = 60000.0 / rrInterval;
        
        if (!hrValid) {
          // First valid reading — set directly
          smoothedHR = instantHR;
          hrValid = true;
        } else {
          // Reject outliers: ignore if >30% different from current
          float diff = abs(instantHR - smoothedHR) / smoothedHR;
          if (diff < 0.3) {
            smoothedHR = smoothedHR * 0.8 + instantHR * 0.2;
          }
        }
        
        heartRate = smoothedHR;
        
        if (rrCount >= 3) {
          hrv = calculateHRV();
        }
      }
    }
    lastPeakTime = now;
  }
}

float calculateHRV() {
  float sum = 0;
  for (int i = 0; i < rrCount; i++) sum += rrIntervals[i];
  float mean = sum / rrCount;
  
  float variance = 0;
  for (int i = 0; i < rrCount; i++) {
    float diff = rrIntervals[i] - mean;
    variance += diff * diff;
  }
  return sqrt(variance / rrCount);
}

void sendData(bool leadsOff) {
  float hr = (leadsOff || !hrValid) ? 0.0 : heartRate;
  float hv = (leadsOff || !hrValid) ? 0.0 : hrv;
  
  // Clamp HR to realistic range
  if (hr > 0 && hr < 40) hr = 0;
  if (hr > 180) hr = 0;
  
  Serial.print("{\"heart_rate\":");
  Serial.print(hr, 1);
  Serial.print(",\"hrv\":");
  Serial.print(hv, 1);
  Serial.print(",\"ecg_raw\":");
  Serial.print(leadsOff ? 0 : analogRead(ECG_PIN));
  Serial.print(",\"leads_off\":");
  Serial.print(leadsOff ? "true" : "false");
  Serial.println("}");
}
