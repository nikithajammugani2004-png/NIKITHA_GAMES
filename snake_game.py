import pygame
import time
import random
import os

# Initialize Pygame
pygame.init()

# Enhanced Colors
BG_COLOR = (20, 25, 40)      
SNAKE_COLOR = (0, 255, 200)   
HEAD_COLOR = (255, 255, 100) # Bright Yellow Head
FOOD_COLOR = (255, 50, 100)   
GRID_COLOR = (30, 35, 50)     
TEXT_COLOR = (255, 255, 255)
LOSE_COLOR = (200, 0, 50)

# Screen Dimensions
box_len = 900
box_height = 600
snake_block = 20  
snake_speed = 8

screen = pygame.display.set_mode((box_len, box_height))
pygame.display.set_caption("NEON SNAKE - HIGH SCORE EDITION")

timer = pygame.time.Clock()
score_font = pygame.font.SysFont("arial", 30, bold=True)

# --- High Score Logic ---
HS_FILE = "highscore.txt"

def get_high_score():
    if not os.path.exists(HS_FILE):
        return 0
    with open(HS_FILE, "r") as f:
        try:
            return int(f.read())
        except:
            return 0

def save_high_score(new_high_score):
    with open(HS_FILE, "w") as f:
        f.write(str(new_high_score))

def draw_grid():
    for x in range(0, box_len, snake_block):
        pygame.draw.line(screen, GRID_COLOR, (x, 0), (x, box_height))
    for y in range(0, box_height, snake_block):
        pygame.draw.line(screen, GRID_COLOR, (0, y), (box_len, y))

def display_scores(score, high_score):
    val = score_font.render(f"SCORE: {score}", True, TEXT_COLOR)
    hs_val = score_font.render(f"HIGH SCORE: {high_score}", True, (255, 215, 0))
    screen.blit(val, [20, 20])
    screen.blit(hs_val, [20, 55])

def make_snake(list_snake):
    # Draw Body
    for i, x in enumerate(list_snake[:-1]):
        color_val = max(100, 255 - (len(list_snake) - i) * 5)
        current_color = (0, color_val, color_val)
        center = (int(x[0] + snake_block/2), int(x[1] + snake_block/2))
        pygame.draw.circle(screen, (0, 50, 50), center, snake_block/1.2)
        pygame.draw.circle(screen, current_color, center, snake_block/2 - 2)

    # Draw Head
    if list_snake:
        head_pos = list_snake[-1]
        head_center = (int(head_pos[0] + snake_block/2), int(head_pos[1] + snake_block/2))
        pygame.draw.circle(screen, (100, 100, 0), head_center, snake_block/1.1)
        pygame.draw.circle(screen, HEAD_COLOR, head_center, snake_block/2)
        pygame.draw.circle(screen, (0, 0, 0), head_center, 3) # Eye

def game_start():
    game_over = False
    game_close = False
    
    high_score = get_high_score()

    val_x1 = round((box_len / 2) / snake_block) * snake_block
    val_y1 = round((box_height / 2) / snake_block) * snake_block
    
    new_x1, new_y1 = 0, 0
    list_snake = []
    snake_len = 1

    foodx = round(random.randrange(0, box_len - snake_block) / snake_block) * snake_block
    foody = round(random.randrange(0, box_height - snake_block) / snake_block) * snake_block
    
    while not game_over:
        while game_close:
            screen.fill(BG_COLOR)
            current_score = snake_len - 1
            if current_score > high_score:
                high_score = current_score
                save_high_score(high_score)
            
            msg = score_font.render("GAME OVER! C-Play Again | Q-Quit", True, LOSE_COLOR)
            screen.blit(msg, [box_len / 5, box_height / 2.5])
            display_scores(current_score, high_score)
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        game_over = True
                        game_close = False
                    if event.key == pygame.K_c:
                        game_start()
                if event.type == pygame.QUIT:
                    game_over = True
                    game_close = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_over = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT and new_x1 == 0:
                    new_x1, new_y1 = -snake_block, 0
                elif event.key == pygame.K_RIGHT and new_x1 == 0:
                    new_x1, new_y1 = snake_block, 0
                elif event.key == pygame.K_UP and new_y1 == 0:
                    new_y1, new_x1 = -snake_block, 0
                elif event.key == pygame.K_DOWN and new_y1 == 0:
                    new_y1, new_x1 = snake_block, 0

        if val_x1 >= box_len or val_x1 < 0 or val_y1 >= box_height or val_y1 < 0:
            game_close = True

        val_x1 += new_x1
        val_y1 += new_y1
        screen.fill(BG_COLOR)
        draw_grid()

        # Food
        food_center = (int(foodx + snake_block/2), int(foody + snake_block/2))
        pygame.draw.circle(screen, FOOD_COLOR, food_center, snake_block/2.5) 

        snake_head = [val_x1, val_y1]
        list_snake.append(snake_head)
        
        if len(list_snake) > snake_len:
            del list_snake[0]

        for x in list_snake[:-1]:
            if x == snake_head:
                game_close = True

        make_snake(list_snake)
        display_scores(snake_len - 1, high_score)
        pygame.display.update()

        if val_x1 == foodx and val_y1 == foody:
            foodx = round(random.randrange(0, box_len - snake_block) / snake_block) * snake_block
            foody = round(random.randrange(0, box_height - snake_block) / snake_block) * snake_block
            snake_len += 1

        timer.tick(snake_speed)

    pygame.quit()
    quit()

if __name__ == "__main__":
    game_start()
