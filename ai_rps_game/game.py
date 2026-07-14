import cv2
import mediapipe as mp
import random
import time
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np


class AIRockPaperScissors:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        
        # Initialize MediaPipe Tasks API
        base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=1,
            min_hand_detection_confidence=0.7,
            running_mode=vision.RunningMode.IMAGE
        )
        self.landmarker = vision.HandLandmarker.create_from_options(options)
        
        self.HAND_CONNECTIONS = [
            (0, 1), (1, 2), (2, 3), (3, 4),
            (0, 5), (5, 6), (6, 7), (7, 8),
            (0, 9), (9, 10), (10, 11), (11, 12),
            (0, 13), (13, 14), (14, 15), (15, 16),
            (0, 17), (17, 18), (18, 19), (19, 20),
            (5, 9), (9, 13), (13, 17), (0, 5), (0, 17)
        ]
        
        self.player_score = 0
        self.computer_score = 0
        self.rounds = 0
        
        self.game_state = "READY"
        self.countdown_start_time = 0
        self.current_countdown = 3
        
        self.player_move = ""
        self.computer_move = ""
        self.result_text = ""
        self.result_color = (255, 255, 255)
        
        # Load the asset images cleanly
        self.assets = {
            "Rock": cv2.imread("assets/rock.png", cv2.IMREAD_UNCHANGED),
            "Paper": cv2.imread("assets/paper.png", cv2.IMREAD_UNCHANGED),
            "Scissors": cv2.imread("assets/scissors.png", cv2.IMREAD_UNCHANGED)
        }
        
        # Initialize modern MediaPipe Image Segmenter for background blur
        seg_base_options = python.BaseOptions(model_asset_path='selfie_segmenter.task')
        seg_options = vision.ImageSegmenterOptions(
            base_options=seg_base_options,
            running_mode=vision.RunningMode.IMAGE
        )
        self.segmenter = vision.ImageSegmenter.create_from_options(seg_options)

    def draw_landmarks(self, frame, hand_landmarks):
        h, w, _ = frame.shape
        pts = []
        for lm in hand_landmarks:
            cx, cy = int(lm.x * w), int(lm.y * h)
            pts.append((cx, cy))
            cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)
            
        for connection in self.HAND_CONNECTIONS:
            start_idx, end_idx = connection
            if start_idx < len(pts) and end_idx < len(pts):
                cv2.line(frame, pts[start_idx], pts[end_idx], (0, 255, 0), 2)

    def detect_gesture(self, hand_landmarks):
        # Improved tracking check based on your video layout
        index_open = hand_landmarks[8].y < hand_landmarks[6].y
        middle_open = hand_landmarks[12].y < hand_landmarks[10].y
        ring_open = hand_landmarks[16].y < hand_landmarks[14].y
        pinky_open = hand_landmarks[20].y < hand_landmarks[18].y
        
        if not index_open and not middle_open and not ring_open and not pinky_open:
            return "Rock"
        if index_open and middle_open and not ring_open and not pinky_open:
            return "Scissors"
        if index_open and middle_open and ring_open and pinky_open:
            return "Paper"
        return "Unknown"

    def evaluate_game(self):
        if self.player_move == "Unknown" or not self.player_move:
            self.result_text = "No Hand Detected!"
            self.result_color = (0, 0, 255)
            return

        self.computer_move = random.choice(["Rock", "Paper", "Scissors"])
        self.rounds += 1

        if self.player_move == self.computer_move:
            self.result_text = "Tie!"
            self.result_color = (0, 255, 255)
        elif (self.player_move == "Rock" and self.computer_move == "Scissors") or \
             (self.player_move == "Paper" and self.computer_move == "Rock") or \
             (self.player_move == "Scissors" and self.computer_move == "Paper"):
            self.result_text = "You Win!"
            self.result_color = (0, 255, 0)
            self.player_score += 1
        else:
            self.result_text = "Computer Wins!"
            self.result_color = (0, 0, 255)
            self.computer_score += 1
            
        # playing rounds until one player reaches 15 points
        if self.player_score >= 6:
            self.game_state = "CHAMPION"

    def overlay_asset(self, frame, img, x_offset, y_offset):
        """Helper to safely blend RGB or RGBA asset images onto the webcam frame"""
        if img is None:
            return
        
        img_h, img_w = img.shape[:2]
        # Safeguard boundaries
        if y_offset + img_h > frame.shape[0] or x_offset + img_w > frame.shape[1]:
            return

        src_area = frame[y_offset:y_offset+img_h, x_offset:x_offset+img_w]

        if img.shape[2] == 4: # Handle PNG transparency layers
            alpha = img[:, :, 3] / 255.0
            for c in range(3):
                src_area[:, :, c] = (1.0 - alpha) * src_area[:, :, c] + alpha * img[:, :, c]
        else: # Regular RGB image fallback
            cv2.copyTo(img[:, :, :3], None, src_area)

    def run(self):
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                break
            
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Define mp_image first so both tools can use it
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            
            # --- BACKGROUND BLUR LOGIC ---
            seg_result = self.segmenter.segment(mp_image)
            
            # Use the confidence mask array
            if seg_result.confidence_masks:
                # Squeeze or slice to get a clean 2D layout (H, W) from (H, W, 1)
                mask = seg_result.confidence_masks[0].numpy_view()[:, :, 0]
                
                # Create the blurred background
                blurred_bg = cv2.GaussianBlur(frame, (55, 55), 0)
                
                # Blend frames dynamically using the float mask values
                mask_3d = np.stack((mask,) * 3, axis=-1)
                frame = (mask_3d * frame + (1.0 - mask_3d) * blurred_bg).astype(np.uint8)
            
            # Detect hand gestures using the same image
            result = self.landmarker.detect(mp_image)
            
            detected_move = ""
            if result.hand_landmarks:
                for hand_landmarks in result.hand_landmarks:
                    self.draw_landmarks(frame, hand_landmarks)
                    detected_move = self.detect_gesture(hand_landmarks)

            if self.game_state == "COUNTDOWN":
                elapsed = time.time() - self.countdown_start_time
                if elapsed < 1:
                    self.current_countdown = 3
                elif elapsed < 2:
                    self.current_countdown = 2
                elif elapsed < 3:
                    self.current_countdown = 1
                else:
                    self.game_state = "SHOW"
                    self.player_move = detected_move if detected_move else "Unknown"
                    self.evaluate_game()
            
            # 1. Main Header
            cv2.rectangle(frame, (0, 0), (w, 50), (40, 40, 40), -1)
            cv2.putText(frame, "AI ROCK PAPER SCISSORS", (w // 2 - 140, 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            
            # 2. Player Display Panel (Left)
            cv2.rectangle(frame, (20, 60), (220, 260), (90, 90, 90), -1)
            p_label = f"You: {self.player_move}" if self.game_state in ["SHOW", "CHAMPION"] else "You:"
            cv2.putText(frame, p_label, (30, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # 3. Computer Display Panel (Right)
            cv2.rectangle(frame, (w - 220, 60), (w - 20, 260), (90, 90, 90), -1)
            c_label = f"Computer: {self.computer_move}" if self.game_state in ["SHOW", "CHAMPION"] else "Computer:"
            cv2.putText(frame, c_label, (w - 210, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
            
            # Render asset graphics on SHOW or CHAMPION states
            if self.game_state in ["SHOW", "CHAMPION"]:
                if self.player_move in self.assets:
                    p_img = cv2.resize(self.assets[self.player_move], (140, 140))
                    self.overlay_asset(frame, p_img, 50, 100)
                
                if self.computer_move in self.assets:
                    c_img = cv2.resize(self.assets[self.computer_move], (140, 140))
                    self.overlay_asset(frame, c_img, w - 190, 100)

            # 4. Central Actions HUD
            if self.game_state == "READY":
                cv2.putText(frame, "Press 'A' to Start Round", (w // 2 - 130, 150),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            elif self.game_state == "COUNTDOWN":
                cv2.putText(frame, str(self.current_countdown), (w // 2 - 20, 150),
                            cv2.FONT_HERSHEY_SIMPLEX, 2.5, (255, 255, 255), 4)
            elif self.game_state == "SHOW":
                cv2.putText(frame, "SHOW", (w // 2 - 60, 110),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 255), 3)
                cv2.putText(frame, self.result_text, (w // 2 - 100, 220),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, self.result_color, 3)
            elif self.game_state == "CHAMPION":
                cv2.rectangle(frame, (40, h // 2 - 80), (320, h // 2 + 40), (0, 150, 0), -1)
                cv2.putText(frame, "CHAMPION", (60, h // 2 - 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 3)
                cv2.putText(frame, "YOU WON THE MATCH!", (60, h // 2 + 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # 5. Live Score Tracker
            cv2.putText(frame, f"Player Score: {self.player_score}", (20, h - 140),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(frame, f"Computer Score: {self.computer_score}", (20, h - 110),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            cv2.putText(frame, f"Rounds: {self.rounds}", (20, h - 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            win_rate = int((self.player_score / self.rounds) * 100) if self.rounds > 0 else 0
            cv2.putText(frame, f"Win Rate: {win_rate}%", (20, h - 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # 6. Navigation Control Legend
            cv2.putText(frame, "A - Again", (w - 220, h - 110),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(frame, "R - Restart Match", (w - 220, h - 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(frame, "Q - Quit", (w - 220, h - 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            cv2.imshow("AI Rock Paper Scissors", frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('a') or key == ord('A'):
                if self.game_state in ["READY", "SHOW"]:
                    self.game_state = "COUNTDOWN"
                    self.countdown_start_time = time.time()
            elif key == ord('r') or key == ord('R'):
                self.player_score = 0
                self.computer_score = 0
                self.rounds = 0
                self.game_state = "READY"
                self.player_move = ""
                self.computer_move = ""
            elif key == ord('q') or key == ord('Q'):
                break
                
        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    game = AIRockPaperScissors()
    game.run()