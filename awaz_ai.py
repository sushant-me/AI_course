import cv2
import mediapipe as mp
import math
import pyttsx3 # Text to Speech Library

# ==========================================
# SETUP
# ==========================================
# 1. Initialize Voice Engine
engine = pyttsx3.init()
engine.setProperty('rate', 150) # Speed of speech

# 2. Initialize AI
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# 3. Config
WIDTH, HEIGHT = 1280, 720
LAST_SPOKEN = ""
LAST_TIME = 0

# ==========================================
# GESTURE RECOGNITION ENGINE (The Logic)
# ==========================================
def get_dist(p1, p2):
    return math.hypot(p1.x - p2.x, p1.y - p2.y)

def detect_gesture(lm):
    # Finger States (0=Folded, 1=Open)
    thumb = 1 if lm[4].x < lm[3].x else 0 # Simple check for right hand
    if lm[4].x > lm[3].x: thumb = 0 # Adjust for hand side if needed
    
    index = 1 if lm[8].y < lm[6].y else 0
    middle = 1 if lm[12].y < lm[10].y else 0
    ring = 1 if lm[16].y < lm[14].y else 0
    pinky = 1 if lm[20].y < lm[18].y else 0
    
    fingers = [thumb, index, middle, ring, pinky]
    
    # Logic Map
    if fingers == [0, 1, 1, 0, 0]: return "VICTORY / PEACE"
    if fingers == [1, 1, 1, 1, 1]: return "HELLO"
    if fingers == [1, 0, 0, 0, 0]: return "YES / OK"
    if fingers == [0, 0, 0, 0, 0]: return "NO / STOP"
    if fingers == [1, 1, 0, 0, 1]: return "I LOVE YOU" # Rock sign + Thumb
    if fingers == [0, 1, 0, 0, 0]: return "ONE"
    
    return "..."

# ==========================================
# MAIN LOOP
# ==========================================
cap = cv2.VideoCapture(0)
cap.set(3, WIDTH)
cap.set(4, HEIGHT)

print("AWAZ AI STARTING...")
engine.say("System Online. Ready to translate.")
engine.runAndWait()

while True:
    success, img = cap.read()
    if not success: continue
    img = cv2.flip(img, 1) # Mirror view
    
    # AI Processing
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)
    
    message = "SHOW HAND"
    col = (255, 255, 255)
    
    if results.multi_hand_landmarks:
        for lms in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(img, lms, mp_hands.HAND_CONNECTIONS)
            
            # 1. Decode Sign
            gesture = detect_gesture(lms.landmark)
            
            # 2. Display
            if gesture != "...":
                message = gesture
                col = (0, 255, 0)
                
                # 3. Speak (Debounce logic)
                import time
                if gesture != LAST_SPOKEN and (time.time() - LAST_TIME) > 2:
                    LAST_SPOKEN = gesture
                    LAST_TIME = time.time()
                    print(f"Speaking: {gesture}")
                    engine.say(gesture)
                    engine.runAndWait()
    
    # UI Design (Glassmorphism)
    # Bottom Bar
    cv2.rectangle(img, (0, HEIGHT-100), (WIDTH, HEIGHT), (30, 30, 30), -1)
    cv2.putText(img, "DETECTED SPEECH:", (50, HEIGHT-40), cv2.FONT_HERSHEY_SIMPLEX, 1, (200, 200, 200), 2)
    cv2.putText(img, message, (400, HEIGHT-40), cv2.FONT_HERSHEY_SIMPLEX, 1.5, col, 3)

    # Top Bar
    cv2.rectangle(img, (0, 0), (WIDTH, 80), (0, 0, 0), -1)
    cv2.putText(img, "AWAZ: SIGN LANGUAGE TRANSLATOR", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

    cv2.imshow("Awaz AI", img)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()