import cv2
import mediapipe as mp

# Initialize MediaPipe Hand tracking components
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7)

# Access your webcam (0 is usually the primary camera)
cap = cv2.VideoCapture(0)

print("Starting video... Look at the pop-up window. Press 'q' to exit.")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        print("Ignoring empty camera frame.")
        continue

    # Mirror the frame horizontally for intuitive movement
    frame = cv2.flip(frame, 1)
    
    # Convert image colors from BGR (OpenCV default) to RGB (MediaPipe requirement)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    # If hands are found, draw the tracking skeleton on the screen
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(
                frame, hand_landmarks, mp_hands.HAND_CONNECTIONS
            )

    # Open an independent graphical window showing the camera feed
    cv2.imshow('MediaPipe Hand Tracker', frame)

    # Stop the program instantly if you press the 'q' key on your keyboard
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Clean up system files and close the camera window
cap.release()
cv2.destroyAllWindows()
