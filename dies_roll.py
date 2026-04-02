import pygame
import random
import sys

# Initialize Pygame
pygame.init()
WIDTH, HEIGHT = 600, 450
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("🔥 Super Pig Dice")
FONT = pygame.font.SysFont("Arial", 28, bold=True)
BIG_FONT = pygame.font.SysFont("Arial", 50, bold=True)
CLOCK = pygame.time.Clock()

# Colors
BG_COLOR = (20, 25, 35)
P1_COLOR = (70, 130, 180) # Steel Blue
P2_COLOR = (220, 20, 60)   # Crimson
GOLD = (255, 215, 0)
WHITE = (255, 255, 255)

def draw_text(text, font, x, y, color=WHITE, center=False):
    img = font.render(text, True, color)
    rect = img.get_rect(topleft=(x, y))
    if center:
        rect.center = (x, y)
    SCREEN.blit(img, rect)

def game_loop():
    # Game State
    player_scores = [0, 0]
    current_turn_score = 0
    current_player = 0
    last_roll = 0
    rolling_anim = 0 # Frames for dice animation
    winner = -1
    WIN_SCORE = 50 # First to 50 wins

    # Button Rects
    roll_btn = pygame.Rect(100, 320, 160, 60)
    hold_btn = pygame.Rect(340, 320, 160, 60)

    while True:
        mouse_pos = pygame.mouse.get_pos()
        SCREEN.fill(BG_COLOR)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            
            if winner == -1: # Only allow clicks if no one has won
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if roll_btn.collidepoint(event.pos):
                        rolling_anim = 15 # Start 15-frame animation
                    
                    if hold_btn.collidepoint(event.pos) and current_turn_score > 0:
                        player_scores[current_player] += current_turn_score
                        if player_scores[current_player] >= WIN_SCORE:
                            winner = current_player
                        else:
                            current_turn_score = 0
                            current_player = (current_player + 1) % 2
            else:
                # Key listener for Win Screen
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r: return True # Restart
                    if event.key == pygame.K_q: return False # Quit

        # Dice Rolling Animation Logic
        if rolling_anim > 0:
            last_roll = random.randint(1, 6)
            rolling_anim -= 1
            if rolling_anim == 0: # Animation finished
                if last_roll == 1:
                    current_turn_score = 0
                    current_player = (current_player + 1) % 2
                else:
                    current_turn_score += last_roll

        # --- DRAW UI ---
        # Player Boxes
        p1_rect = pygame.Rect(30, 30, 240, 100)
        p2_rect = pygame.Rect(330, 30, 240, 100)
        
        # Highlight current player
        pygame.draw.rect(SCREEN, P1_COLOR if current_player == 0 else (50, 50, 50), p1_rect, border_radius=10)
        pygame.draw.rect(SCREEN, P2_COLOR if current_player == 1 else (50, 50, 50), p2_rect, border_radius=10)
        
        draw_text(f"PLAYER 1", FONT, 150, 55, WHITE, True)
        draw_text(f"Score: {player_scores[0]}", FONT, 150, 95, WHITE, True)
        
        draw_text(f"PLAYER 2", FONT, 450, 55, WHITE, True)
        draw_text(f"Score: {player_scores[1]}", FONT, 450, 95, WHITE, True)

        # Center Dice / Turn Area
        if winner == -1:
            draw_text(f"TURN SCORE: {current_turn_score}", FONT, WIDTH//2, 180, GOLD, True)
            # Draw Dice
            dice_color = (0, 255, 100) if last_roll > 1 else (255, 50, 50)
            if last_roll > 0:
                pygame.draw.rect(SCREEN, dice_color, (WIDTH//2-40, 210, 80, 80), border_radius=10)
                draw_text(str(last_roll), BIG_FONT, WIDTH//2, 250, (0,0,0), True)

            # Draw Buttons with Hover Effect
            r_color = (70, 180, 70) if roll_btn.collidepoint(mouse_pos) else (50, 140, 50)
            h_color = (200, 150, 50) if hold_btn.collidepoint(mouse_pos) else (170, 130, 40)
            
            pygame.draw.rect(SCREEN, r_color, roll_btn, border_radius=15)
            pygame.draw.rect(SCREEN, h_color, hold_btn, border_radius=15)
            draw_text("ROLL DICE", FONT, 180, 350, WHITE, True)
            draw_text("HOLD", FONT, 420, 350, WHITE, True)
        else:
            # Win Screen Overlay
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            SCREEN.blit(overlay, (0,0))
            draw_text(f"PLAYER {winner + 1} WINS!", BIG_FONT, WIDTH//2, 180, GOLD, True)
            draw_text("Press 'R' to Restart or 'Q' to Quit", FONT, WIDTH//2, 260, WHITE, True)

        pygame.display.flip()
        CLOCK.tick(60)

# Main entry point to handle restarts
while True:
    if not game_loop():
        break

pygame.quit()
