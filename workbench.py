import cv2
import time
import math
import mediapipe as mp
import numpy as np

# ==========================================
# CONFIGURATION & ASSETS
# ==========================================
WIDTH, HEIGHT = 1280, 720
CURRENT_SCENE = "MENU"
GAME_OVER = False
FAIL_REASON = ""

# COLORS (Industrial Palette)
C_BG = (30, 30, 30)
C_PANEL = (50, 60, 70)
C_DANGER = (0, 0, 200)   # Red
C_SAFE = (0, 200, 0)     # Green
C_WARN = (0, 200, 255)   # Yellow
C_TEXT = (255, 255, 255)
C_ACCENT = (255, 100, 0) # Orange

# AI SETUP
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.8)
mp_draw = mp.solutions.drawing_utils

# ==========================================
# SYSTEM CLASSES (The "Engine")
# ==========================================
class Graphics:
    @staticmethod
    def draw_box(img, box, color, alpha=0.6, filled=True):
        x1, y1, x2, y2 = box
        overlay = img.copy()
        if filled:
            cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
            cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)
        cv2.rectangle(img, (x1, y1), (x2, y2), (200, 200, 200), 2)

    @staticmethod
    def draw_text(img, text, x, y, size=0.8, color=C_TEXT):
        cv2.putText(img, text, (x+2, y+2), cv2.FONT_HERSHEY_SIMPLEX, size, (0,0,0), 3)
        cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, size, color, 2)

    @staticmethod
    def draw_tool_icon(img, name, x, y):
        # Procedurally draw icons so no external files needed
        c = (200, 200, 200)
        if name == "WRENCH":
            cv2.line(img, (x+20, y+60), (x+60, y+20), c, 8)
            cv2.circle(img, (x+60, y+20), 15, c, -1)
            cv2.circle(img, (x+60, y+20), 8, (50,50,50), -1)
        elif name == "MULTI":
            cv2.rectangle(img, (x+25, y+15), (x+55, y+65), (0, 200, 255), -1)
            cv2.rectangle(img, (x+30, y+20), (x+50, y+40), (0,0,0), -1)
        elif name == "TAG":
            cv2.rectangle(img, (x+25, y+15), (x+55, y+65), (0, 0, 255), -1)
            cv2.circle(img, (x+40, y+25), 5, (255,255,255), -1)
        elif name == "VALVE":
            cv2.circle(img, (x+40, y+40), 25, (0, 0, 255), 3)
            cv2.line(img, (x+15, y+40), (x+65, y+40), (0,0,255), 3)

class ToolBelt:
    def __init__(self):
        self.tools = []
        self.selected = None
        self.grab_timer = 0
    
    def set_loadout(self, tool_names):
        self.tools = tool_names
        self.selected = None

    def update(self, img, cursor, is_grabbing):
        h, w, c = img.shape
        Graphics.draw_box(img, [100, h-100, w-100, h], (20, 20, 20), 0.8)
        
        spacing = 150
        start_x = (w - (len(self.tools) * spacing)) // 2
        
        for i, name in enumerate(self.tools):
            bx = start_x + (i * spacing)
            by = h - 90
            
            # Hover & Select Logic
            if bx < cursor[0] < bx+100 and by < cursor[1] < by+80:
                cv2.rectangle(img, (bx, by), (bx+100, by+80), (100, 100, 100), -1)
                if is_grabbing:
                    self.selected = name
            
            # Draw Slot
            col = (0, 255, 0) if self.selected == name else (255, 255, 255)
            cv2.rectangle(img, (bx, by), (bx+100, by+80), col, 2)
            Graphics.draw_tool_icon(img, name, bx+10, by)
            Graphics.draw_text(img, name, bx+10, by-10, 0.5)

# ==========================================
# JOB 1: HV ELECTRICIAN (The "Death Trap")
# ==========================================
# Sequence: Lockout -> Test -> Open -> Replace -> Unlock
elec = {"step": 0, "timer": 0}

def run_elec(img, cursor, is_grab, tools):
    global GAME_OVER, FAIL_REASON
    
    # 1. DRAW SCENE (Industrial Panel)
    Graphics.draw_box(img, [300, 150, 900, 550], C_PANEL)
    
    # Main Breaker Handle
    handle_col = C_SAFE if elec["step"] >= 1 else C_DANGER
    handle_y = 250 if elec["step"] >= 1 else 350
    cv2.rectangle(img, (200, 200), (280, 400), (30,30,30), -1) # Track
    cv2.circle(img, (240, handle_y), 30, handle_col, -1) # Handle
    Graphics.draw_text(img, "415V MAIN", 180, 430, 0.6)

    # Lockout Hole
    cv2.circle(img, (240, 250), 10, (0,0,0), -1)
    if elec["step"] >= 2:
        Graphics.draw_tool_icon(img, "TAG", 215, 225) # Draw Tag applied
    
    # Panel Door
    if elec["step"] < 4:
        Graphics.draw_box(img, [400, 200, 800, 500], (60, 70, 80)) # Closed
        Graphics.draw_text(img, "DANGER: HIGH VOLTAGE", 450, 350, 1.0, C_DANGER)
    else:
        # Open Panel (Internal Components)
        Graphics.draw_box(img, [400, 200, 800, 500], (20, 20, 20)) # Dark inside
        # Fuses
        for i in range(3):
            fx = 450 + (i*120)
            col = (200, 200, 200)
            if i == 1 and elec["step"] < 6: col = (50, 50, 50) # Burnt Middle Fuse
            if i == 1 and elec["step"] == 5: col = (20, 20, 20) # Empty Slot
            cv2.rectangle(img, (fx, 250), (fx+60, 450), col, -1)
            cv2.putText(img, "HV", (fx+10, 350), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1)

    # 2. INTERACTION LOGIC (The Hard Part)
    cx, cy = cursor
    
    # BREAKER LOGIC
    if 200 < cx < 280 and 200 < cy < 400 and is_grab:
        if tools.selected == None: # Hand
            if elec["step"] == 0: elec["step"] = 1 # Off
            elif elec["step"] == 1: elec["step"] = 0 # On (Mistake)
        elif tools.selected == "TAG":
            if elec["step"] == 1: elec["step"] = 2 # Locked
            elif elec["step"] == 0: 
                GAME_OVER = True; FAIL_REASON = "CANNOT LOCK LIVE BREAKER!"

    # DOOR LOGIC
    if 400 < cx < 800 and 200 < cy < 500 and elec["step"] < 4:
        # If trying to open...
        if is_grab and tools.selected == None:
            if elec["step"] == 0: # Live
                GAME_OVER = True; FAIL_REASON = "ARC FLASH! FATAL SHOCK."
            elif elec["step"] == 1: # Off but not locked
                GAME_OVER = True; FAIL_REASON = "VIOLATION: NO LOCKOUT TAG."
            elif elec["step"] == 2:
                elec["step"] = 4 # Open Safe

    # FUSE LOGIC (Middle Fuse)
    if elec["step"] >= 4 and 570 < cx < 630 and 250 < cy < 450:
        if tools.selected == "MULTI":
            Graphics.draw_text(img, "0.0V (DEAD)", cx, cy, 0.8, C_SAFE)
            # Just verify, don't change step yet
        elif tools.selected == "WRENCH": # Using wrench to pull fuse
            if is_grab:
                elec["step"] = 5 # Pulled
        elif tools.selected == "FUSE" and elec["step"] == 5:
            if is_grab:
                elec["step"] = 6 # Fixed!
                Graphics.draw_text(img, "SYSTEM RESTORED", 400, 600, 1.5, C_SAFE)

# ==========================================
# JOB 2: INDUSTRIAL PLUMBER (Pressure Logic)
# ==========================================
plumb = {"pressure": 150, "valve": 0, "fixed": 0}

def run_plumb(img, cursor, is_grab, tools):
    global GAME_OVER, FAIL_REASON
    
    # 1. DRAW SCENE
    # Pressure Gauge
    cx, cy = 300, 300
    cv2.circle(img, (cx, cy), 80, (220, 220, 220), -1)
    
    # Needle Logic
    angle = 180 if plumb["pressure"] > 0 else 0
    ex = int(cx + 60 * math.cos(math.radians(angle)))
    ey = int(cy - 60 * math.sin(math.radians(angle)))
    cv2.line(img, (cx, cy), (ex, ey), C_DANGER, 4)
    Graphics.draw_text(img, f"{plumb['pressure']} PSI", cx-40, cy+110, 0.8, C_DANGER if plumb["pressure"]>0 else C_SAFE)

    # Valve Wheel
    vx, vy = 600, 300
    col = C_SAFE if plumb["valve"] == 1 else C_DANGER
    cv2.circle(img, (vx, vy), 60, col, 8)
    cv2.line(img, (vx-60, vy), (vx+60, vy), col, 8)
    Graphics.draw_text(img, "ISOLATION VALVE", vx-80, vy+90, 0.6)

    # The Pipe Leak
    lx, ly = 900, 300
    Graphics.draw_box(img, [800, 280, 1000, 320], (100, 100, 100))
    if plumb["fixed"] == 0:
        # Spray Animation
        cv2.line(img, (lx, ly), (lx+40, ly-60), (255, 200, 0), 2)
        cv2.line(img, (lx, ly), (lx-20, ly-80), (255, 200, 0), 2)
        Graphics.draw_text(img, "LEAK!", lx-30, ly-50, 1.0, C_DANGER)
    else:
        Graphics.draw_text(img, "SEALED", lx-30, ly-50, 1.0, C_SAFE)

    # 2. LOGIC
    mx, my = cursor
    
    # Valve Interaction
    if 540 < mx < 660 and 240 < my < 360 and is_grab:
        if tools.selected == "VALVE": # Must use valve tool
            plumb["valve"] = 1
            plumb["pressure"] = 0
    
    # Leak Interaction
    if 800 < mx < 1000 and 200 < my < 400 and is_grab:
        if tools.selected == "WRENCH":
            if plumb["pressure"] > 0:
                GAME_OVER = True; FAIL_REASON = "EXPLOSION! PRESSURE TOO HIGH."
            else:
                plumb["fixed"] = 1


# ==========================================
# MAIN LOOP
# ==========================================
cap = cv2.VideoCapture(0)
cap.set(3, WIDTH)
cap.set(4, HEIGHT)

belt = ToolBelt()

while True:
    success, img = cap.read()
    if not success: continue
    img = cv2.flip(img, 1)
    
    # HAND TRACKING
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)
    
    cursor = (0, 0)
    is_grab = False
    
    if results.multi_hand_landmarks:
        lms = results.multi_hand_landmarks[0]
        mp_draw.draw_landmarks(img, lms, mp_hands.HAND_CONNECTIONS)
        
        # Cursor is Index Finger Tip
        ix, iy = int(lms.landmark[8].x * WIDTH), int(lms.landmark[8].y * HEIGHT)
        cursor = (ix, iy)
        
        # Grab is Fist Check (Tip close to Wrist)
        dist = math.hypot(ix - int(lms.landmark[0].x * WIDTH), iy - int(lms.landmark[0].y * HEIGHT))
        is_grab = dist < 150 # Threshold for "Fist"
        
        # Draw Cursor
        col = (0, 255, 0) if is_grab else (0, 255, 255)
        cv2.circle(img, (ix, iy), 15, col, 2)
        if is_grab: cv2.circle(img, (ix, iy), 10, col, -1)

    # GAME OVER SCREEN
    if GAME_OVER:
        Graphics.draw_box(img, [0, 0, WIDTH, HEIGHT], (0, 0, 0), 0.9)
        Graphics.draw_text(img, "CERTIFICATION FAILED", 350, 300, 2.0, C_DANGER)
        Graphics.draw_text(img, FAIL_REASON, 400, 400, 1.0, C_TEXT)
        Graphics.draw_text(img, "Grab to Retry", 550, 500, 1.0, C_WARN)
        if is_grab: 
            GAME_OVER = False
            elec["step"] = 0
            plumb["pressure"] = 150
            plumb["valve"] = 0
            plumb["fixed"] = 0
            CURRENT_SCENE = "MENU"

    # SCENE LOGIC
    elif CURRENT_SCENE == "MENU":
        Graphics.draw_text(img, "DAKSHYA ENTERPRISE", 400, 150, 1.5, C_ACCENT)
        Graphics.draw_text(img, "Select Certification:", 500, 250, 0.8)
        
        # Buttons
        Graphics.draw_box(img, [300, 300, 600, 450], C_PANEL)
        Graphics.draw_text(img, "HV ELECTRICIAN", 340, 390, 0.8)
        
        Graphics.draw_box(img, [700, 300, 1000, 450], C_PANEL)
        Graphics.draw_text(img, "IND. PLUMBER", 760, 390, 0.8)
        
        if is_grab:
            if 300 < cursor[0] < 600 and 300 < cursor[1] < 450:
                CURRENT_SCENE = "ELEC"
                belt.set_loadout(["TAG", "MULTI", "WRENCH", "FUSE"])
            elif 700 < cursor[0] < 1000 and 300 < cursor[1] < 450:
                CURRENT_SCENE = "PLUMB"
                belt.set_loadout(["VALVE", "WRENCH"])

    elif CURRENT_SCENE == "ELEC":
        run_elec(img, cursor, is_grab, belt)
        belt.update(img, cursor, is_grab)
        # Back Button
        Graphics.draw_box(img, [1100, 20, 1250, 70], (50, 50, 50))
        Graphics.draw_text(img, "MENU", 1140, 60, 0.8)
        if 1100 < cursor[0] < 1250 and 20 < cursor[1] < 70 and is_grab: CURRENT_SCENE = "MENU"

    elif CURRENT_SCENE == "PLUMB":
        run_plumb(img, cursor, is_grab, belt)
        belt.update(img, cursor, is_grab)
        # Back Button
        Graphics.draw_box(img, [1100, 20, 1250, 70], (50, 50, 50))
        Graphics.draw_text(img, "MENU", 1140, 60, 0.8)
        if 1100 < cursor[0] < 1250 and 20 < cursor[1] < 70 and is_grab: CURRENT_SCENE = "MENU"

    cv2.imshow("Dakshya Enterprise", img)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()