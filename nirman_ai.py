import cv2
import numpy as np
import math

# --- CONFIGURATION ---
WIDTH, HEIGHT = 1280, 720
CURRENT_MODE = "MENU"
REPORT = {"Cracks": "N/A", "Verticality": "N/A"}

# --- COLORS ---
C_RED = (0, 0, 255)    # Danger
C_GREEN = (0, 255, 0)  # Safe
C_YELLOW = (0, 255, 255) # Warning
C_BLACK = (0, 0, 0)
C_WHITE = (255, 255, 255)

# --- UTILS ---
def draw_ui(img, title, instruction):
    # Top Bar
    cv2.rectangle(img, (0, 0), (WIDTH, 80), C_BLACK, -1)
    cv2.putText(img, "NIRMAN AI: STRUCTURAL AUDITOR", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, C_WHITE, 2)
    
    # Bottom Bar
    cv2.rectangle(img, (0, HEIGHT-80), (WIDTH, HEIGHT), C_BLACK, -1)
    cv2.putText(img, instruction, (20, HEIGHT-30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, C_YELLOW, 2)
    
    # Mode Title
    cv2.putText(img, f"MODE: {title}", (WIDTH-300, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, C_GREEN, 2)

def detect_cracks(img):
    # 1. Convert to Gray
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 2. Blur to remove noise
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # 3. Canny Edge Detection (The "Crack" finder)
    edges = cv2.Canny(blur, 50, 150)
    
    # 4. Find Contours
    contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    crack_severity = "SAFE"
    max_width = 0
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 100: # Ignore small noise
            x, y, w, h = cv2.boundingRect(cnt)
            
            # Logic: If it's long and thin, it's a crack
            aspect_ratio = float(w)/h if h>0 else 0
            if aspect_ratio < 0.2 or aspect_ratio > 5:
                # Draw the crack
                cv2.drawContours(img, [cnt], -1, C_RED, 2)
                
                # Measure "width" (approximation)
                current_width = min(w, h)
                if current_width > max_width: max_width = current_width
    
    # Civil Engineering Logic
    if max_width == 0:
        crack_severity = "NO CRACKS"
        col = C_GREEN
    elif max_width < 5:
        crack_severity = "HAIRLINE (PLASTER ONLY)"
        col = C_YELLOW
    else:
        crack_severity = "STRUCTURAL FAILURE (EVACUATE)"
        col = C_RED
        
    cv2.putText(img, f"STATUS: {crack_severity}", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, col, 3)
    return crack_severity

def check_verticality(img):
    # This simulates a "Plumb Bob" using image lines
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    
    # Hough Line Transform (Finds straight lines)
    lines = cv2.HoughLines(edges, 1, np.pi/180, 200)
    
    status = "SEARCHING FOR PILLAR..."
    col = C_WHITE
    
    if lines is not None:
        for rho, theta in lines[0]:
            a = np.cos(theta)
            b = np.sin(theta)
            x0 = a*rho
            y0 = b*rho
            x1 = int(x0 + 1000*(-b))
            y1 = int(y0 + 1000*(a))
            x2 = int(x0 - 1000*(-b))
            y2 = int(y0 - 1000*(a))
            
            # Draw the line found
            cv2.line(img, (x1,y1), (x2,y2), (255, 0, 0), 2)
            
            # Calculate Angle in Degrees
            angle = math.degrees(theta)
            
            # Vertical means angle is near 0 or 180 (Vertical lines in Hough are 0 theta)
            # Note: OpenCV Hough theta=0 is vertical line.
            
            deviation = abs(angle - 0)
            if deviation > 90: deviation = abs(deviation - 180)
            
            # Civil Engineering Tolerance: 90 degrees +/- 1 degree
            if deviation < 2:
                status = f"PERFECTLY VERTICAL (Dev: {deviation:.1f} deg)"
                col = C_GREEN
            elif deviation < 5:
                status = f"WARNING: LEANING (Dev: {deviation:.1f} deg)"
                col = C_YELLOW
            else:
                status = f"DANGER: UNSTABLE (Dev: {deviation:.1f} deg)"
                col = C_RED
            
            # Visual Plumb Line (Reference)
            cv2.line(img, (WIDTH//2, 0), (WIDTH//2, HEIGHT), C_GREEN, 1)

    cv2.putText(img, status, (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, col, 3)
    return status

# ==========================================
# MAIN LOOP
# ==========================================
cap = cv2.VideoCapture(0)
cap.set(3, WIDTH)
cap.set(4, HEIGHT)

while True:
    success, img = cap.read()
    if not success: continue
    
    # Mode Selector
    if CURRENT_MODE == "MENU":
        cv2.rectangle(img, (0,0), (WIDTH, HEIGHT), C_BLACK, -1)
        cv2.putText(img, "NIRMAN AI", (450, 200), cv2.FONT_HERSHEY_SIMPLEX, 2, C_WHITE, 4)
        cv2.putText(img, "Sustainable Infrastructure Audit", (380, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.8, C_GREEN, 1)
        
        cv2.rectangle(img, (200, 400), (500, 500), (50, 50, 50), -1)
        cv2.putText(img, "1. CRACK CHECK", (230, 460), cv2.FONT_HERSHEY_SIMPLEX, 0.7, C_WHITE, 2)
        
        cv2.rectangle(img, (700, 400), (1000, 500), (50, 50, 50), -1)
        cv2.putText(img, "2. VERTICALITY", (730, 460), cv2.FONT_HERSHEY_SIMPLEX, 0.7, C_WHITE, 2)
        
        cv2.putText(img, "Press [1] or [2] on Keyboard", (450, 600), cv2.FONT_HERSHEY_SIMPLEX, 0.8, C_YELLOW, 2)
        
        key = cv2.waitKey(1)
        if key == ord('1'): CURRENT_MODE = "CRACK"
        if key == ord('2'): CURRENT_MODE = "VERT"

    elif CURRENT_MODE == "CRACK":
        result = detect_cracks(img)
        draw_ui(img, "CRACK DETECTOR", "Point at a wall. 'Q' to Quit, 'M' for Menu.")
        
        key = cv2.waitKey(1)
        if key == ord('q'): break
        if key == ord('m'): CURRENT_MODE = "MENU"

    elif CURRENT_MODE == "VERT":
        result = check_verticality(img)
        draw_ui(img, "DIGITAL PLUMB BOB", "Align pillar with screen center. 'Q' to Quit.")
        
        key = cv2.waitKey(1)
        if key == ord('q'): break
        if key == ord('m'): CURRENT_MODE = "MENU"

    cv2.imshow("Nirman AI - Hult Prize", img)

cap.release()
cv2.destroyAllWindows()