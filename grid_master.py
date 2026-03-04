import cv2
import numpy as np
import time
import random

from workbench import C_SAFE

# ==========================================
# CONFIGURATION & PHYSICS
# ==========================================
WIDTH, HEIGHT = 1280, 720
GAME_STATE = "MENU" # MENU, RUNNING, BLACKOUT
START_TIME = 0

# COLORS (SCADA Palette)
C_BG = (10, 10, 15)       # Dark Background
C_LINE_OFF = (50, 50, 50) # Dead Line
C_LINE_ON = (0, 255, 0)   # Healthy Line
C_WARN = (0, 255, 255)    # Overload
C_DANGER = (0, 0, 255)    # Trip/Fail
C_TEXT = (200, 200, 200)
C_ACCENT = (255, 100, 0)

# GRID PHYSICS
FREQUENCY = 50.00 # Target: 50.00 Hz
VOLTAGE = 230.00  # Target: 230 kV
TOTAL_LOAD = 0
TOTAL_GEN = 0
STABILITY = 100 # %

# ==========================================
# SYSTEM CLASSES
# ==========================================
class Node:
    def __init__(self, name, x, y, type, mw, critical=False):
        self.name = name
        self.pos = (x, y)
        self.type = type # "GEN" (Generator) or "LOAD" (Consumer)
        self.mw = mw # Megawatts (Capacity for Gen, Demand for Load)
        self.active = True
        self.critical = critical # If True, cannot be cut easily
        self.temp = 50 # Temperature (Overheat simulation)

    def draw(self, img, is_hover):
        # Color Logic
        col = C_LINE_OFF
        if self.active:
            if self.type == "GEN": col = C_ACCENT # Generators are Orange
            else: col = C_LINE_ON # Loads are Green
            
            if self.type == "LOAD" and self.critical: col = (255, 50, 255) # Hospitals are Purple
        
        # Hover Effect
        radius = 40
        if is_hover: 
            cv2.circle(img, self.pos, radius+5, (255, 255, 255), 2)
            # Show Info Box
            info = f"{self.name}: {self.mw} MW"
            cv2.putText(img, info, (self.pos[0]-40, self.pos[1]-50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, C_TEXT, 2)

        # Draw Node
        cv2.circle(img, self.pos, radius, col, -1)
        cv2.circle(img, self.pos, radius, (200, 200, 200), 2)
        
        # Icon/Text
        label = "G" if self.type == "GEN" else "L"
        if self.critical: label = "H"
        cv2.putText(img, label, (self.pos[0]-10, self.pos[1]+10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2)
        
        # Status Text
        status = "ON" if self.active else "OFF"
        cv2.putText(img, f"{status}", (self.pos[0]-20, self.pos[1]+60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, col, 1)

class GridSystem:
    def __init__(self):
        # Define the Nepal Grid Map
        self.nodes = [
            Node("Marsyangdi Hydro", 200, 360, "GEN", 120),
            Node("Kulekhani Hydro", 200, 550, "GEN", 80),
            Node("Kathmandu City", 600, 360, "LOAD", 100), # Residential
            Node("Hetauda Ind.", 600, 550, "LOAD", 90),    # Industrial
            Node("Teaching Hospital", 900, 360, "LOAD", 20, critical=True),
            Node("Baneshwor Sub", 900, 550, "LOAD", 40)
        ]
        # Define Connections (Lines)
        self.lines = [
            (0, 2), # Marsyangdi -> Ktm
            (1, 3), # Kulekhani -> Hetauda
            (2, 4), # Ktm -> Hospital
            (2, 5), # Ktm -> Baneshwor
            (3, 5)  # Hetauda -> Baneshwor (Ring Main)
        ]
        self.events = []
        self.last_event = time.time()

    def update(self):
        global FREQUENCY, STABILITY, GAME_STATE
        
        # 1. Calculate Supply vs Demand
        supply = sum(n.mw for n in self.nodes if n.type == "GEN" and n.active)
        demand = sum(n.mw for n in self.nodes if n.type == "LOAD" and n.active)
        
        # 2. Physics Engine
        net = supply - demand
        
        # Frequency Drift (Real physics: Inertia)
        # If Supply > Demand, Freq rises. If Supply < Demand, Freq drops.
        drift = (net / 100.0) * 0.1 
        FREQUENCY += drift
        
        # Natural damping (Grid tries to stabilize)
        FREQUENCY += (50.0 - FREQUENCY) * 0.05
        
        # Random Fluctuations (Noise)
        FREQUENCY += random.uniform(-0.02, 0.02)
        
        # 3. Fail Conditions
        if FREQUENCY < 48.5 or FREQUENCY > 51.5:
            GAME_STATE = "BLACKOUT"
        
        # 4. Random Events (The "Hard" Part)
        if time.time() - self.last_event > 5: # Every 5 seconds
            event_roll = random.randint(0, 100)
            if event_roll > 70: # 30% chance
                target = random.choice([n for n in self.nodes if n.type=="LOAD"])
                surge = random.randint(10, 30)
                target.mw += surge
                self.events.append(f"SURGE: {target.name} +{surge}MW Demand!")
                self.last_event = time.time()

    def toggle_node(self, idx):
        # Operator Logic: Cannot turn off Generators easily (Ramp down takes time)
        # Can turn off Loads instantly (Load Shedding)
        node = self.nodes[idx]
        if node.type == "LOAD":
            node.active = not node.active
            return f"SWITCHED {node.name}: {'ON' if node.active else 'OFF'}"
        return "CANNOT TRIP GENERATOR MANUALLY"

# ==========================================
# GRAPHICS ENGINE
# ==========================================
def draw_dashboard(img, grid, mouse_pos):
    # 1. Draw Connections (Lines)
    for start_idx, end_idx in grid.lines:
        n1 = grid.nodes[start_idx]
        n2 = grid.nodes[end_idx]
        
        # Line Physics
        col = C_LINE_OFF
        thickness = 2
        if n1.active and n2.active:
            col = C_LINE_ON # Powered
            thickness = 4
            # Simulation: Current Flow animation
            if int(time.time() * 10) % 2 == 0: col = (100, 255, 100)
            
        cv2.line(img, n1.pos, n2.pos, col, thickness)

    # 2. Draw Nodes
    hover_idx = -1
    for i, node in enumerate(grid.nodes):
        dist = np.linalg.norm(np.array(node.pos) - np.array(mouse_pos))
        is_hover = dist < 40
        if is_hover: hover_idx = i
        node.draw(img, is_hover)

    # 3. Draw HUD (Heads Up Display)
    # Frequency Gauge (The most critical metric)
    cv2.rectangle(img, (20, 20), (300, 150), (20, 20, 25), -1)
    cv2.rectangle(img, (20, 20), (300, 150), C_TEXT, 2)
    
    col = C_SAFE
    if abs(50 - FREQUENCY) > 0.5: col = C_WARN
    if abs(50 - FREQUENCY) > 1.0: col = C_DANGER
    
    cv2.putText(img, "GRID FREQUENCY", (40, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, C_TEXT, 1)
    cv2.putText(img, f"{FREQUENCY:.2f} Hz", (40, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.5, col, 3)

    # Alerts Log
    cv2.rectangle(img, (900, 20), (1260, 200), (20, 20, 25), -1)
    cv2.putText(img, "SYSTEM LOGS", (920, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, C_ACCENT, 1)
    y = 80
    for event in grid.events[-4:]: # Show last 4
        cv2.putText(img, event, (920, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, C_TEXT, 1)
        y += 25

    return hover_idx

# ==========================================
# MAIN APP
# ==========================================
cv2.namedWindow("GridMaster AI")
grid = GridSystem()
mouse_pos = (0, 0)

def mouse_callback(event, x, y, flags, param):
    global mouse_pos
    mouse_pos = (x, y)
    if event == cv2.EVENT_LBUTTONDOWN:
        # Check clicks
        idx = draw_dashboard(np.zeros((HEIGHT, WIDTH, 3), np.uint8), grid, (x,y))
        if idx != -1:
            log = grid.toggle_node(idx)
            grid.events.append(log)

cv2.setMouseCallback("GridMaster AI", mouse_callback)

while True:
    img = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    
    if GAME_STATE == "MENU":
        cv2.putText(img, "GRIDMASTER AI", (350, 300), cv2.FONT_HERSHEY_SIMPLEX, 2, C_ACCENT, 4)
        cv2.putText(img, "National Load Dispatch Simulator", (380, 360), cv2.FONT_HERSHEY_SIMPLEX, 0.8, C_TEXT, 1)
        cv2.putText(img, "Press [SPACE] to Initialize Grid", (400, 500), cv2.FONT_HERSHEY_SIMPLEX, 0.8, C_WARN, 2)
        
        key = cv2.waitKey(1)
        if key == 32: # Space
            GAME_STATE = "RUNNING"
            grid = GridSystem()

    elif GAME_STATE == "RUNNING":
        grid.update()
        draw_dashboard(img, grid, mouse_pos)
        
        # Instructions
        cv2.putText(img, "INSTRUCTIONS: Click Green Nodes (Loads) to Shed Power. Keep Freq at 50Hz.", (20, 680), cv2.FONT_HERSHEY_SIMPLEX, 0.6, C_TEXT, 1)

    elif GAME_STATE == "BLACKOUT":
        cv2.rectangle(img, (0,0), (WIDTH, HEIGHT), (0,0,0), -1)
        cv2.putText(img, "GRID COLLAPSE", (350, 300), cv2.FONT_HERSHEY_SIMPLEX, 2, C_DANGER, 4)
        cv2.putText(img, f"Final Freq: {FREQUENCY:.2f} Hz", (480, 380), cv2.FONT_HERSHEY_SIMPLEX, 1, C_TEXT, 2)
        cv2.putText(img, "Press [R] to Reboot System", (450, 500), cv2.FONT_HERSHEY_SIMPLEX, 0.8, C_WARN, 2)
        
        key = cv2.waitKey(1)
        if key == ord('r'):
            GAME_STATE = "MENU"
            FREQUENCY = 50.00

    cv2.imshow("GridMaster AI", img)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cv2.destroyAllWindows()