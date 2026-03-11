import cv2
import mediapipe as mp
import time

# 1. Setup MediaPipe for Hand Tracking
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# 2. Start Webcam
cap = cv2.VideoCapture(0)
cap.set(3, 1280) # Width
cap.set(4, 720)  # Height

# 3. AuraCraft Inventory & State Variables
inventory_mangoes = 50
inventory_spices = 50
jars_made = 0

holding_mango = False
holding_spice = False

feedback_msg = "AR INSTRUCTOR: Show hand to start Pickle Making."
feedback_color = (0, 255, 255) # Yellow

# Define 3 UI Zones for the Pickle Process
ZONE_MANGO = (50, 250, 300, 500)   # Left: Raw Veg/Mango
ZONE_SPICE = (490, 250, 740, 500)  # Center: Spices
ZONE_JAR = (930, 250, 1180, 500)   # Right: Final Jar

while True:
    success, img = cap.read()
    if not success:
        break
        
    # Flip image so it acts like a mirror
    img = cv2.flip(img, 1)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Process hands
    results = hands.process(img_rgb)
    
    # ---------------------------------------------------
    # DRAW THE AR UI HOLOGRAPHS (Semi-transparent)
    # ---------------------------------------------------
    overlay = img.copy()
    
    # Draw Mango Zone (Green)
    cv2.rectangle(overlay, (ZONE_MANGO[0], ZONE_MANGO[1]), (ZONE_MANGO[2], ZONE_MANGO[3]), (0, 200, 0), -1)
    # Draw Spice Zone (Red/Orange)
    cv2.rectangle(overlay, (ZONE_SPICE[0], ZONE_SPICE[1]), (ZONE_SPICE[2], ZONE_SPICE[3]), (0, 100, 255), -1)
    # Draw Jar Zone (Blue)
    cv2.rectangle(overlay, (ZONE_JAR[0], ZONE_JAR[1]), (ZONE_JAR[2], ZONE_JAR[3]), (255, 100, 0), -1)
    
    # Blend overlay with original image (30% transparency)
    cv2.addWeighted(overlay, 0.3, img, 0.7, 0, img)
    
    # ---------------------------------------------------
    # DRAW THE RAW MATERIALS (Visual Shapes)
    # ---------------------------------------------------
    # Mango Holograms (Green Circles)
    cv2.circle(img, (175, 375), 40, (0, 255, 0), 3)
    cv2.putText(img, "RAW MANGO", (ZONE_MANGO[0]+20, ZONE_MANGO[1]+40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    # Spice Holograms (Red Dots)
    for i in range(5):
        cv2.circle(img, (580 + (i*15), 375), 5, (0, 0, 255), -1)
    cv2.putText(img, "SPICES (50g)", (ZONE_SPICE[0]+20, ZONE_SPICE[1]+40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    # Jar Hologram (White Box)
    cv2.rectangle(img, (1000, 320), (1110, 450), (255, 255, 255), 3)
    cv2.putText(img, "SEAL JAR", (ZONE_JAR[0]+50, ZONE_JAR[1]+40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    # ---------------------------------------------------
    # HAND TRACKING & LOGIC
    # ---------------------------------------------------
    if results.multi_hand_landmarks:
        for hand_lms in results.multi_hand_landmarks:
            # Draw the glowing dots on the hand
            mp_draw.draw_landmarks(img, hand_lms, mp_hands.HAND_CONNECTIONS)
            
            # Get the tip of the Index Finger
            index_finger = hand_lms.landmark[8]
            h, w, c = img.shape
            cx, cy = int(index_finger.x * w), int(index_finger.y * h)
            
            # Draw a bright cursor on the index finger
            cv2.circle(img, (cx, cy), 15, (0, 255, 255), cv2.FILLED)
            
            # STATE 1: Grab Mango
            if ZONE_MANGO[0] < cx < ZONE_MANGO[2] and ZONE_MANGO[1] < cy < ZONE_MANGO[3]:
                if not holding_mango and not holding_spice and inventory_mangoes > 0:
                    holding_mango = True
                    feedback_msg = "Excellent! Mango grabbed. Now drag to Spices."
                    feedback_color = (0, 255, 255) # Yellow
            
            # STATE 2: Mix Spices
            if ZONE_SPICE[0] < cx < ZONE_SPICE[2] and ZONE_SPICE[1] < cy < ZONE_SPICE[3]:
                if holding_mango and not holding_spice and inventory_spices > 0:
                    holding_spice = True
                    feedback_msg = "Doing good! Spices added. Move to Jar to seal."
                    feedback_color = (0, 200, 255) # Orange
            
            # STATE 3: Seal Jar
            if ZONE_JAR[0] < cx < ZONE_JAR[2] and ZONE_JAR[1] < cy < ZONE_JAR[3]:
                if holding_mango and holding_spice:
                    # Reset hand state and update inventory
                    holding_mango = False
                    holding_spice = False
                    inventory_mangoes -= 1
                    inventory_spices -= 1
                    jars_made += 1
                    
                    feedback_msg = "PERFECT QUALITY! Jar Sealed! +Rs 20 Profit."
                    feedback_color = (0, 255, 0) # Bright Green

    # ---------------------------------------------------
    # UI TEXT: DASHBOARD & FEEDBACK
    # ---------------------------------------------------
    cv2.rectangle(img, (0, 0), (1280, 100), (0, 0, 0), -1) # Top black bar
    cv2.putText(img, "AuraCraft AR: Traditional Pickle Processing", (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 200, 255), 3)
    
    # Inventory Display
    cv2.putText(img, f"Raw Materials: {inventory_mangoes}kg", (950, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(img, f"Jars Ready: {jars_made}", (950, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # Dynamic Feedback Message (Bottom)
    cv2.rectangle(img, (0, 620), (1280, 720), (0, 0, 0), -1) # Bottom black bar
    cv2.putText(img, feedback_msg, (50, 680), cv2.FONT_HERSHEY_SIMPLEX, 1.2, feedback_color, 3)

    # Show the video
    cv2.imshow("AuraCraft AR Simulation", img)
    
    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()