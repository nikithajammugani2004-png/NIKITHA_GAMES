from flask import Flask, render_template, Response, request, jsonify
import cv2
import mediapipe as mp
import numpy as np
import copy
import time

app = Flask(__name__)

# --- INITIALIZE MEDIAPIPE ---
# Hand Tracking for Drawing
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.5, # Slightly dropped to prevent line breaks during fast tracking
    min_tracking_confidence=0.7
)

mp_draw = mp.solutions.drawing_utils

# Canvas States Engine
imgCanvas = None
xp, yp = 0, 0
was_drawing = False

# --- SMOOTHING ENGINE VARIABLES ---
# Increased for high-speed tracking responsiveness to eliminate fast writing lag
SMOOTH_FACTOR = 0.65 
sm_x, sm_y = 0, 0

# Historic Stacks for Undo / Redo
undo_stack = []
redo_stack = []
MAX_HISTORY = 20

# Configurable Global Variables Controlled by Frontend UI
current_color = (127, 0, 255) 
saved_color = (127, 0, 255)  
brush_size = 5
active_mode = "Drawing"
show_camera = True
show_skeleton = True
isolate_hand = False  # Dynamic toggle mode flag variable

## Timer configuration for auto-clear gesture
palm_start_time = None
last_palm_pos = None

# Global Shared Video Capture Instance (Prevents UI toggles from deadlocking the camera)
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

def save_to_history():
    global imgCanvas, undo_stack, redo_stack
    if imgCanvas is not None:
        if len(undo_stack) >= MAX_HISTORY:
            undo_stack.pop(0)
        undo_stack.append(copy.deepcopy(imgCanvas))
        redo_stack.clear()

def create_hand_mask(frame_shape, landmarks, w, h):
    """
    Creates a generous, clean mask tracking exclusively the hand landmarks,
    with custom dilation padding so edges aren't dropped during fast movement.
    """
    hand_mask = np.zeros(frame_shape[:2], dtype=np.uint8)
    
    if landmarks:
        landmark_coords = []
        for lm in landmarks:
            landmark_coords.append((int(lm.x * w), int(lm.y * h)))
        landmark_coords = np.array(landmark_coords)
        
        # Build hull and expand it cleanly with a high padding radius
        hull = cv2.convexHull(landmark_coords)
        cv2.drawContours(hand_mask, [hull], -1, (255), thickness=cv2.FILLED)
        
        # Strong dilation expands mask outward to capture fingers completely
        kernel = np.ones((35, 35), np.uint8)
        hand_mask = cv2.dilate(hand_mask, kernel, iterations=1)
        hand_mask = cv2.GaussianBlur(hand_mask, (15, 15), 0)

    return hand_mask

def apply_segmentation(frame, hand_mask):
    """
    Crops out the entire body frame background, keeping ONLY the isolated 
    hand tracking window over a clean black canvas background.
    """
    h, w, c = frame.shape
    blank_bg = np.zeros((h, w, 3), np.uint8)
    
    # Convert single-channel mask to color dimensions
    hand_mask_bgr = cv2.cvtColor(hand_mask, cv2.COLOR_GRAY2BGR)
    normalized_mask = hand_mask_bgr.astype(float) / 255.0
    
    # Isolate hand texture directly without body model interference
    foreground = cv2.multiply(normalized_mask, frame.astype(float))
    background = cv2.multiply(1.0 - normalized_mask, blank_bg.astype(float))
    
    return cv2.add(foreground, background).astype(np.uint8)

def generate_frames():
    global xp, yp, sm_x, sm_y, imgCanvas, current_color, saved_color, brush_size, active_mode, show_camera, show_skeleton, was_drawing, palm_start_time, last_palm_pos, cap
    
    # Safely re-open hardware if it closed down unexpectedly 
    if not cap.isOpened():
        cap.open(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    while True:
        success, frame = cap.read()
        if not success:
            break
            
        frame = cv2.flip(frame, 1)
        h, w, c = frame.shape
        
        # Initialize canvas if it doesn't exist
        if imgCanvas is None:
            imgCanvas = np.zeros((h, w, 3), np.uint8)
            # Commit first clear state to history
            undo_stack.append(copy.deepcopy(imgCanvas))

        # MediaPipe processing requires RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # PROCESS FRAME: Hands Landmark Detection
        rgb_frame.flags.writeable = False
        hand_results = hands.process(rgb_frame)
        rgb_frame.flags.writeable = True

        # Initialize clean blank hand mask frame window
        final_hand_mask = np.zeros((h, w), dtype=np.uint8)

        # Draw hand features and track landmarks
        if hand_results.multi_hand_landmarks:
            # We are limiting max_num_hands=1 during initialization
            for hand_landmarks in hand_results.multi_hand_landmarks:
                # 1. Optionally draw the MediaPipe skeleton/connections
                if show_skeleton:
                    mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                
                landmarks = hand_landmarks.landmark
                
                # --- CREATE CROPPED HAND MASK ---
                final_hand_mask = create_hand_mask(frame.shape, landmarks, w, h)
                
                # --- DETECT INDIVIDUAL FINGER STATES ---
                index_up  = landmarks[8].y  < landmarks[6].y
                middle_up = landmarks[12].y < landmarks[10].y
                ring_up   = landmarks[16].y < landmarks[14].y
                pinky_up  = landmarks[20].y < landmarks[18].y
                thumb_up  = landmarks[4].x  < landmarks[3].x if landmarks[17].x > landmarks[5].x else landmarks[4].x > landmarks[3].x
                
                # Extract raw coordinates
                raw_x, raw_y = int(landmarks[8].x * w), int(landmarks[8].y * h)

                # --- SMOOTHING MATRIX ---
                if sm_x == 0 and sm_y == 0:
                    sm_x, sm_y = raw_x, raw_y
                else:
                    sm_x = sm_x + SMOOTH_FACTOR * (raw_x - sm_x)
                    sm_y = sm_y + SMOOTH_FACTOR * (raw_y - sm_y)

                # Final processed coordinates
                cx, cy = int(sm_x), int(sm_y)

                # --- GESTURE DECISION MATRIX ---
                
                # 1. OPEN PALM -> Targeted Eraser / Auto-Clear Hold
                if index_up and middle_up and ring_up and pinky_up:
                    active_mode = "Targeted Eraser"
                    if was_drawing:
                        save_to_history()
                        was_drawing = False
                    
                    current_color = (0, 0, 0)
                    active_brush = 160
                    
                    # Auto-Clear tracking logic: Check if hand is held relatively still
                    if palm_start_time is None:
                        palm_start_time = time.time()
                        last_palm_pos = (cx, cy)
                    else:
                        # Check distance from last frame position
                        dist = np.sqrt((cx - last_palm_pos[0])**2 + (cy - last_palm_pos[1])**2)
                        if dist < 15: # Hand is holding still
                            elapsed = time.time() - palm_start_time
                            countdown = max(0, int(2 - elapsed))
                            if countdown > 0:
                                cv2.putText(frame, f"CLEARING CANVAS IN: {countdown}", (cx - 80, cy - 50), 
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                            if elapsed >= 1.5: # Trigger auto-clear after 1.5 seconds
                                save_to_history()
                                imgCanvas.fill(0)
                                palm_start_time = None
                        else:
                            # Hand moved too much, reset timer
                            palm_start_time = time.time()
                            last_palm_pos = (cx, cy)
                    
                    cv2.circle(frame, (cx, cy), 30, (255, 255, 255), 2)
                    cv2.line(imgCanvas, (xp, yp) if xp != 0 else (cx, cy), (cx, cy), current_color, active_brush)
                    xp, yp = cx, cy

                # 2. THUMB + INDEX -> Hover / Move
                elif index_up and thumb_up and not middle_up and not ring_up and not pinky_up:
                    palm_start_time = None # Reset auto-clear timer
                    active_mode = "Hover / Move"
                    if was_drawing:
                        save_to_history()
                        was_drawing = False
                    
                    current_color = saved_color
                    xp, yp = 0, 0 
                    
                    # Enhanced HUD: Draw exact brush size preview outline with a crosshair center
                    cv2.circle(frame, (cx, cy), int(brush_size / 2), current_color, 2)
                    cv2.circle(frame, (cx, cy), 2, (0, 255, 0), cv2.FILLED)
                    
                    # Live Text Stats Overlay on the frame
                    cv2.putText(frame, f"Brush Size: {brush_size}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    cv2.putText(frame, f"Mode: {active_mode}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (168, 85, 247), 2)

                # 3. INDEX UP ONLY -> Precise Drawing
                elif index_up and not middle_up and not ring_up and not pinky_up:
                    active_mode = "Drawing"
                    was_drawing = True
                    current_color = saved_color
                    
                    cv2.circle(frame, (cx, cy), int(brush_size/2) + 3, current_color, cv2.FILLED)
                    
                    if xp == 0 or yp == 0:
                        xp, yp = cx, cy
                        
                    # Calculate fast movement velocity
                    movement_speed = np.sqrt((cx - xp)**2 + (cy - yp)**2)
                    
                    # If jumping fast but continuous, interpolate intermediate steps to prevent broken segments
                    if movement_speed > 60 and xp != 0:
                        steps = int(movement_speed / 10)
                        for i in range(1, steps + 1):
                            inter_x = int(xp + (cx - xp) * (i / steps))
                            inter_y = int(yp + (cy - yp) * (i / steps))
                            cv2.line(imgCanvas, (xp, yp), (inter_x, inter_y), current_color, brush_size)
                            xp, yp = inter_x, inter_y
                    
                    cv2.line(imgCanvas, (xp, yp), (cx, cy), current_color, brush_size)
                    xp, yp = cx, cy

                # 4. CLOSED FIST -> Pause Drawing
                elif not index_up and not middle_up and not ring_up and not pinky_up:
                    active_mode = "Pause Drawing"
                    if was_drawing:
                        save_to_history()
                        was_drawing = False
                    # Stop tracking coordinates
                    xp, yp = 0, 0 
                    sm_x, sm_y = 0, 0 # Reset filter memory
                
                else:
                    # Keep previous coordinates briefly to maintain line continuity if gesture drops for a single frame
                    pass

        else:
            if was_drawing:
                save_to_history()
                was_drawing = False
            xp, yp = 0, 0
            sm_x, sm_y = 0, 0

        # --- APPLY BODY REMOVAL / SEGMENTATION ---
        # --- APPLY BODY REMOVAL / SEGMENTATION ---
        if isolate_hand:
            # Isolates exclusively the hand area dynamically using the tracking hull coordinates
            segmented_frame = apply_segmentation(frame, final_hand_mask)
            frame = segmented_frame

        # Toggle final display background
        if not show_camera:
            # Entire background is black, landmarks/isolated hand are removed
            frame = np.zeros((h, w, 3), np.uint8)

        # --- HIGH-FIDELITY CANVASS MASK BLENDING ---
        # Seamlessly combine digital paint (imgCanvas) with isolated camera feed (frame)
        
        # 1. Create a binary mask of the canvas painting (white paint on black background)
        imgGray = cv2.cvtColor(imgCanvas, cv2.COLOR_BGR2GRAY)
        # Every pixel above 1 (not black) becomes white (255)
        _, imgMask = cv2.threshold(imgGray, 1, 255, cv2.THRESH_BINARY)
        # Create inverse mask (everything NOT paint becomes white)
        imgMaskInv = cv2.bitwise_not(imgMask)
        
        # 2. Convert mask dimensions back to BGR for multi-channel multiplication
        imgMaskBGR = cv2.cvtColor(imgMask, cv2.COLOR_GRAY2BGR)
        imgMaskInvBGR = cv2.cvtColor(imgMaskInv, cv2.COLOR_GRAY2BGR)

        # 3. Blend: Remove pixels from camera feed where paint exists
        frame_background = cv2.bitwise_and(frame, imgMaskInvBGR)
        
        # 4. Final Addition: Overlay digital paint onto masked background
        final_blended_frame = cv2.bitwise_or(frame_background, imgCanvas)

        # Draw the visual highlight overlay after everything else is combined so it's always on top
        if active_mode == "Targeted Eraser" and hand_results.multi_hand_landmarks:
            eraser_radius = 80  # Exactly matches active_brush / 2
            
            # Create a dedicated overlay space for the semi-transparent glow effect
            overlay = final_blended_frame.copy()
            # Draw a filled circle highlighting the eraser's footprint shape (Translucent pink/red)
            cv2.circle(overlay, (cx, cy), eraser_radius, (127, 0, 255), cv2.FILLED)
            # Blend the alpha overlay into the final frame output layer
            cv2.addWeighted(overlay, 0.25, final_blended_frame, 0.75, 0, final_blended_frame)
            
            # Draw a sharp outer circle border ring and precise center dot alignment guide
            cv2.circle(final_blended_frame, (cx, cy), eraser_radius, (255, 255, 255), 2)
            cv2.circle(final_blended_frame, (cx, cy), 4, (255, 255, 255), cv2.FILLED)

        ret, buffer = cv2.imencode('.jpg', final_blended_frame)
        frame_bytes = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/set_config', methods=['POST'])
def set_config():
    global current_color, saved_color, brush_size, show_camera, show_skeleton, imgCanvas, undo_stack, redo_stack
    data = request.json
    
    if 'color' in data:
        # Flask receives '#RRGGBB' hex, OpenCV needs (B, G, R) tuples
        hex_color = data['color'].lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        # Keep internal color state for drawing
        saved_color = (rgb[2], rgb[1], rgb[0]) 
        current_color = saved_color
        
    if 'size' in data:
        brush_size = int(data['size'])
        
    if 'show_camera' in data:
        show_camera = data['show_camera']
        
    if 'show_skeleton' in data:
        show_skeleton = data['show_skeleton']
        
    if 'isolate_hand' in data:
        global isolate_hand
        # Convert incoming frontend string/boolean cleanly into a Python boolean value
        isolate_hand = str(data['isolate_hand']).lower() == 'true'
        
    if 'action' in data:
        action = data['action']
        if action == 'clear':
            if imgCanvas is not None:
                save_to_history()
                # Entirely reset digital canvas to black
                imgCanvas.fill(0)
        elif action == 'undo':
            # Need at least current state and one historic state to step back
            if len(undo_stack) > 1:
                # Store present state to redo stack
                redo_stack.append(undo_stack.pop())
                # Restore previous state
                imgCanvas = copy.deepcopy(undo_stack[-1])
        elif action == 'redo':
            if len(redo_stack) > 0:
                next_state = redo_stack.pop()
                undo_stack.append(next_state)
                imgCanvas = copy.deepcopy(next_state)
            
    return jsonify({"status": "success"})
 
@app.route('/get_mode')
def get_mode():
    global active_mode
    return jsonify({"mode": active_mode})

if __name__ == "__main__":
    # Ensure optimal port and disable debug auto-reloader for opencv stability
    app.run(debug=True, port=5500, use_reloader=False)