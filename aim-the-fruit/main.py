import math
import random
import time
import pygame

# Initialize Pygame
pygame.init()

# Window Configuration
WIDTH, HEIGHT = 800, 800
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Fruit Aim Trainer")

# Constants
TARGET_INCREMENT = 1000
TARGET_EVENT = pygame.USEREVENT
TARGET_PADDING = 40
TOP_BAR_HEIGHT = 110 
GAME_DURATION = 60 

# Colors
BG_COLOR = (10, 20, 30)
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
LABEL_FONT = pygame.font.SysFont("comicsans", 22)
TITLE_FONT = pygame.font.SysFont("comicsans", 40)

class Target:
    MAX_SIZE = 35
    GROWTH_RATE = 0.2

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 0
        self.grow = True
        self.fruit_type = random.randint(0, 3)
        
        if self.fruit_type == 0: self.points = 10
        elif self.fruit_type == 1: self.points = 20
        elif self.fruit_type == 2: self.points = 50
        else: self.points = 100

    def update(self):
        if self.size + self.GROWTH_RATE >= self.MAX_SIZE:
            self.grow = False
        if self.grow:
            self.size += self.GROWTH_RATE
        else:
            self.size -= self.GROWTH_RATE

    def draw(self, win):
        if self.size <= 0: return
        if self.fruit_type == 0: # Apple
            pygame.draw.circle(win, (200, 0, 0), (self.x, self.y), self.size)
            pygame.draw.rect(win, (100, 60, 20), (self.x-2, self.y-self.size-4, 4, 8))
        elif self.fruit_type == 1: # Orange
            pygame.draw.circle(win, (255, 140, 0), (self.x, self.y), self.size)
            pygame.draw.circle(win, (34, 139, 34), (self.x+2, self.y-self.size-2), self.size//3)
        elif self.fruit_type == 2: # Grape
            pygame.draw.circle(win, (128, 0, 128), (self.x, self.y), self.size)
            pygame.draw.circle(win, (180, 80, 255), (self.x-self.size//4, self.y-self.size//4), self.size//3)
        elif self.fruit_type == 3: # Watermelon
            pygame.draw.circle(win, (34, 139, 34), (self.x, self.y), self.size)
            pygame.draw.circle(win, (200, 30, 30), (self.x, self.y), self.size * 0.8)
            pygame.draw.line(win, (10, 80, 10), (self.x - self.size, self.y), (self.x + self.size, self.y), 2)

    def collide(self, x, y):
        dis = math.sqrt((x - self.x)**2 + (y - self.y)**2)
        return dis <= self.size

def format_time(secs):
    milli = math.floor(int(secs * 1000 % 1000) / 100)
    seconds = int(secs % 60)
    return f"{seconds:02d}.{milli}"

def draw_top_bar(win, remaining_time, score, counts, misses):
    pygame.draw.rect(win, (180, 180, 180), (0, 0, WIDTH, TOP_BAR_HEIGHT))
    time_label = LABEL_FONT.render(f"TIME: {format_time(remaining_time)}", 1, COLOR_BLACK)
    score_label = TITLE_FONT.render(f"SCORE: {score}", 1, (0, 50, 150))
    win.blit(time_label, (20, 10))
    win.blit(score_label, (WIDTH//2 - score_label.get_width()//2, 5))
    
    fruits = [
        (f"Apples: {counts['apple']}", (180, 0, 0), 40),
        (f"Oranges: {counts['orange']}", (150, 80, 0), 220),
        (f"Grapes: {counts['grape']}", (100, 0, 100), 400),
        (f"Melons: {counts['melon']}", (0, 100, 0), 580)
    ]
    for text, color, x_pos in fruits:
        lbl = LABEL_FONT.render(text, 1, color)
        win.blit(lbl, (x_pos, 70))
    
    miss_lbl = LABEL_FONT.render(f"Missed: {misses}", 1, (50, 50, 50))
    win.blit(miss_lbl, (650, 10))

def end_screen(win, score, counts, hits, clicks):
    win.fill(BG_COLOR)
    accuracy = round(hits / max(1, clicks) * 100, 1)
    
    texts = [
        ("GAME OVER", (255, 0, 0), 80, TITLE_FONT),
        (f"Final Score: {score}", COLOR_WHITE, 180, LABEL_FONT),
        (f"Apples: {counts['apple']} | Oranges: {counts['orange']}", (200, 200, 200), 240, LABEL_FONT),
        (f"Grapes: {counts['grape']} | Melons: {counts['melon']}", (200, 200, 200), 280, LABEL_FONT),
        (f"Accuracy: {accuracy}%", COLOR_WHITE, 340, LABEL_FONT),
        ("Press 'R' to Restart or 'Q' to Quit", (255, 255, 0), 450, LABEL_FONT)
    ]

    for text, color, y, font in texts:
        label = font.render(text, 1, color)
        win.blit(label, (WIDTH/2 - label.get_width()/2, y))

    pygame.display.update()
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return True # Signal to restart
                if event.key == pygame.K_q:
                    return False # Signal to quit

def main():
    while True: # Outer loop for restarts
        run = True
        targets = []
        clock = pygame.time.Clock()
        score, hits, clicks, misses = 0, 0, 0, 0
        counts = {"apple": 0, "orange": 0, "grape": 0, "melon": 0}
        
        MAX_TARGETS = 5
        start_time = time.time()
        pygame.time.set_timer(TARGET_EVENT, TARGET_INCREMENT)

        restart = False
        while run:
            clock.tick(60)
            click_occurred = False
            mouse_pos = pygame.mouse.get_pos()
            
            remaining_time = max(0, GAME_DURATION - (time.time() - start_time))
            if remaining_time <= 0:
                restart = end_screen(WIN, score, counts, hits, clicks)
                run = False
                break

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); exit()
                if event.type == TARGET_EVENT:
                    if len(targets) < MAX_TARGETS:
                        x = random.randint(TARGET_PADDING, WIDTH - TARGET_PADDING)
                        y = random.randint(TARGET_PADDING + TOP_BAR_HEIGHT, HEIGHT - TARGET_PADDING)
                        targets.append(Target(x, y))
                if event.type == pygame.MOUSEBUTTONDOWN:
                    click_occurred = True
                    clicks += 1

            for target in targets[:]:
                target.update()
                if target.size <= 0:
                    targets.remove(target)
                    misses += 1
                elif click_occurred and target.collide(*mouse_pos):
                    if target.fruit_type == 0: counts["apple"] += 1
                    elif target.fruit_type == 1: counts["orange"] += 1
                    elif target.fruit_type == 2: counts["grape"] += 1
                    elif target.fruit_type == 3: counts["melon"] += 1
                    score += target.points
                    hits += 1
                    targets.remove(target)
                    click_occurred = False

            WIN.fill(BG_COLOR)
            for target in targets: target.draw(WIN)
            draw_top_bar(WIN, remaining_time, score, counts, misses)
            pygame.display.update()

        if not restart:
            break

    pygame.quit()

if __name__ == "__main__":
    main()
