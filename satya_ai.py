import cv2
import mediapipe as mp
import numpy as np
import time
import math

# ==========================================
# CONFIGURATION
# ==========================================
WIDTH, HEIGHT = 1280, 720
STRESS_THRESHOLD = 65 # Score above this = LIE
SESSION_TIME = 30 # Seconds to survive the interrogation

# COLORS (Cyberpunk Palette)
C_BG = (10, 10, 20)
C_GRID = (30, 30, 50)
C_CYAN = (255, 200, 0) # Main HUD
C_RED = (0, 0, 255) # Danger
C_GREEN = (0, 255, 0) # Safe
C_WHITE = (200, 200, 200)

# AI SETUP
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.8,
    min_tracking_confidence=0.8
)

# ==========================================
# BIOMETRIC ENGINE (The Deep Math)
# ==========================================
class Biometrics:
    def __init__(self):
        self.blinks = 0
        self.last_blink_time = 0
        self.blink_rate = 0 # Blinks per minute
        self.gaze_deviations = 0 # How often eyes shift
        self.stress_score = 0
        self.start_time = time.time()
        self.eye_closed = False
        self.history = [] # For graphing

    def update(self, landmarks, img_w, img_h):
        # 1. BLINK DETECTION (EAR Logic)
        # Left Eye indices
        l_top = landmarks[159]
        l_bot = landmarks[145]
        l_dist = math.hypot(l_top.x - l_bot.x, l_top.y - l_bot.y)
        
        # Right Eye indices
        r_top = landmarks[386]
        r_bot = landmarks[374]
        r_dist = math.hypot(r_top.x - r_bot.x, r_top.y - r_bot.y)
        
        avg_dist = (l_dist + r_dist) / 2.0

        if avg_dist < 0.012: # Eyes closed
            if not self.eye_closed:
                self.blinks += 1
                self.last_blink_time = time.time()
                self.eye_closed = True
        else:
            self.eye_closed = False

        # Calculate BPM (Blinks Per Minute) - Moving Average
        elapsed = time.time() - self.start_time
        if elapsed > 0:
            self.blink_rate = (self.blinks / elapsed) * 60

        # 2. GAZE TRACKING (Iris vs Eye Center)
        # Left Iris Center (468) vs Eye Corners (33, 133)
        iris = landmarks[468]
        eye_left = landmarks[33]
        eye_right = landmarks[133]
        
        # Horizontal ratio
        eye_width = eye_right.x - eye_left.x
        iris_rel = (iris.x - eye_left.x) / eye_width
        
        # Normal gaze is 0.45 - 0.55. Anything else is "Shifty"
        gaze_stress = 0
        if iris_rel < 0.40 or iris_rel > 0.60: # Looking Left/Right
            self.gaze_deviations += 1
            gaze_stress = 20

        # 3. CALCULATE STRESS SCORE
        # Normal blink rate is 10-15. High is > 25.
        blink_stress = max(0, (self.blink_rate - 15) * 2)
        
        # Combine metrics
        raw_score = blink_stress + gaze_stress + (self.gaze_deviations * 0.5)
        self.stress_score = min(100, int(raw_score))
        self.history.append(self.stress_score)
        if len(self.history) > 100: self.history.pop(0)

# ==========================================
# VISUALIZATION ENGINE (The HUD)
# ==========================================
def draw_hud(img, bio):
    h, w, c = img.shape
    
    # 1. RETICLE (Targeting System)
    center_x, center_y = w // 2, h // 2
    cv2.line(img, (center_x-20, center_y), (center_x+20, center_y), C_CYAN, 1)
    cv2.line(img, (center_x, center_y-20), (center_x, center_y+20), C_CYAN, 1)
    cv2.circle(img, (center_x, center_y), 100, C_GRID, 1)

    # 2. DATA COLUMNS (Left Side)
    cv2.rectangle(img, (20, 100), (250, 400), (0,0,0), -1)
    cv2.rectangle(img, (20, 100), (250, 400), C_CYAN, 1)
    
    cv2.putText(img, "BIOMETRIC FEED", (30, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.6, C_CYAN, 1)
    
    # Blink Data
    cv2.putText(img, f"BLINK RATE: {int(bio.blink_rate)}", (30, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.5, C_WHITE, 1)
    col = C_GREEN if bio.blink_rate < 20 else C_RED
    cv2.rectangle(img, (30, 180), (30 + int(bio.blink_rate * 2), 190), col, -1)

    # Gaze Data
    cv2.putText(img, f"GAZE SHIFTS: {bio.gaze_deviations}", (30, 230), cv2.FONT_HERSHEY_SIMPLEX, 0.5, C_WHITE, 1)
    
    # 3. LIVE STRESS GRAPH (Bottom)
    cv2.rectangle(img, (300, 600), (980, 700), (0,0,0), -1)
    cv2.rectangle(img, (300, 600), (980, 700), C_GRID, 1)
    cv2.putText(img, "LIVE STRESS TENSOR", (310, 620), cv2.FONT_HERSHEY_SIMPLEX, 0.5, C_CYAN, 1)
    
    if len(bio.history) > 1:
        points = []
        for i, val in enumerate(bio.history):
            x = 300 + int(i * (680 / 100))
            y = 700 - val
            points.append((x, y))
        
        cv2.polylines(img, [np.array(points)], False, C_CYAN, 2)

    # 4. VERDICT (Top Center)
    elapsed = int(time.time() - bio.start_time)
    remaining = max(0, SESSION_TIME - elapsed)
    
    cv2.putText(img, f"T-MINUS: {remaining}s", (w//2 - 80, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, C_WHITE, 2)
    
    if bio.stress_score > STRESS_THRESHOLD:
        cv2.rectangle(img, (w//2 - 200, 80), (w//2 + 200, 160), C_RED, -1)
        cv2.putText(img, "DECEPTION DETECTED", (w//2 - 180, 130), cv2.FONT_HERSHEY_SIMPLEX, 1, C_WHITE, 3)
    else:
        cv2.rectangle(img, (w//2 - 100, 80), (w//2 + 100, 130), C_GREEN, -1)
        cv2.putText(img, "TRUTHFUL", (w//2 - 80, 120), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2)

def draw_eye_tracking(img, landmarks):
    h, w, c = img.shape
    # Draw digital circles on eyes
    left_iris = landmarks[468]
    right_iris = landmarks[473]
    
    lx, ly = int(left_iris.x * w), int(left_iris.y * h)
    rx, ry = int(right_iris.x * w), int(right_iris.y * h)
    
    # Sci-fi crosshairs
    cv2.circle(img, (lx, ly), 5, C_RED, -1)
    cv2.circle(img, (lx, ly), 15, C_CYAN, 1)
    cv2.line(img, (lx-20, ly), (lx+20, ly), C_CYAN, 1)
    
    cv2.circle(img, (rx, ry), 5, C_RED, -1)
    cv2.circle(img, (rx, ry), 15, C_CYAN, 1)
    cv2.line(img, (rx-20, ry), (rx+20, ry), C_CYAN, 1)


# ==========================================
# MAIN LOOP
# ==========================================
cap = cv2.VideoCapture(0)
cap.set(3, WIDTH)
cap.set(4, HEIGHT)

bio = Biometrics()

print("SATYA AI INITIALIZED. INTERROGATION STARTING.")

while True:
    success, img = cap.read()
    if not success: continue
    
    # Mirror image for user comfort
    img = cv2.flip(img, 1)
    
    # Face Mesh
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(img_rgb)
    
    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            lms = face_landmarks.landmark
            
            # Update Biometrics
            bio.update(lms, WIDTH, HEIGHT)
            
            # Draw Graphics
            draw_eye_tracking(img, lms)
            draw_hud(img, bio)
            
    # Final Result Screen
    if time.time() - bio.start_time > SESSION_TIME:
        cv2.rectangle(img, (0,0), (WIDTH, HEIGHT), C_BG, -1)
        
        final_verdict = "SUBJECT TRUTHFUL"
        col = C_GREEN
        if bio.stress_score > 50: 
            final_verdict = "SUBJECT DECEPTIVE"
            col = C_RED
            
        cv2.putText(img, "INTERROGATION COMPLETE", (300, 300), cv2.FONT_HERSHEY_SIMPLEX, 1.5, C_WHITE, 2)
        cv2.putText(img, final_verdict, (350, 450), cv2.FONT_HERSHEY_SIMPLEX, 2, col, 4)
        
        cv2.putText(img, "Press 'R' to Reset", (500, 600), cv2.FONT_HERSHEY_SIMPLEX, 1, C_WHITE, 1)
        
        if cv2.waitKey(1) & 0xFF == ord('r'):
            bio = Biometrics()

    cv2.imshow("SATYA AI - Polygraph", img)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()