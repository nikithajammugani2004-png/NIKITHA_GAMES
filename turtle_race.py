import turtle
import time
import random

WIDTH, HEIGHT = 700, 600
COLORS = ['red', 'green', 'blue', 'orange', 'yellow', 'black', 'purple', 'pink', 'brown', 'cyan']

def get_number_of_racers():
    while True:
        racers = input('Enter the number of racers (2 - 10): ')
        if racers.isdigit():
            racers = int(racers)
            if 2 <= racers <= 10:
                return racers
            print('Number not in range 2-10. Try Again!')
        else:
            print('Input is not numeric... Try Again!')

def draw_finish_line():
    line = turtle.Turtle()
    line.speed(0)
    line.penup()
    line.goto(-WIDTH//2 + 20, HEIGHT//2 - 40)
    line.pendown()
    line.forward(WIDTH - 40)
    line.hideturtle()

def countdown():
    counter = turtle.Turtle()
    counter.hideturtle()
    counter.penup()
    for i in range(3, 0, -1):
        counter.write(str(i), align="center", font=("Arial", 88, "bold"))
        time.sleep(1)
        counter.clear()
    counter.write("GO!", align="center", font=("Arial", 48, "bold"))
    time.sleep(0.5)
    counter.clear()

def create_turtles(colors):
    turtles = []
    spacingx = WIDTH // (len(colors) + 1)
    for i, color in enumerate(colors):
        racer = turtle.Turtle()
        racer.color(color)
        racer.shape('turtle')
        racer.left(90)
        racer.penup()
        racer.setpos(-WIDTH//2 + (i + 1) * spacingx, -HEIGHT//2 + 30)
        racer.showturtle()
        turtles.append(racer)
    return turtles

def race(colors):
    turtles = create_turtles(colors)
    draw_finish_line()
    countdown()

    while True:
        for racer in turtles:
            distance = random.randrange(1, 20)
            racer.forward(distance)

            x, y = racer.pos()
            # Finish line is at HEIGHT/2 - 40
            if y >= HEIGHT // 2 - 40:
                winner_color = colors[turtles.index(racer)]
                victory_dance(racer, winner_color)
                return winner_color

def victory_dance(racer, color):
    # Make the winner spin and grow!
    for _ in range(8):
        racer.right(45)
        racer.shapesize(2, 2)
    
    announcer = turtle.Turtle()
    announcer.hideturtle()
    announcer.penup()
    announcer.goto(0, 0)
    announcer.color(color)
    announcer.write(f"THE {color.upper()} TURTLE WINS!", align="center", font=("Arial", 24, "bold"))

def init_turtle():
    screen = turtle.Screen()
    screen.setup(WIDTH, HEIGHT)
    screen.title('Turtle Racing Championship!')

if __name__ == "__main__":
    racers = get_number_of_racers()
    init_turtle()

    random.shuffle(COLORS)
    selected_colors = COLORS[:racers]

    winner = race(selected_colors)
    print("The winner is the turtle with color:", winner)
    
    # Keeps window open until clicked
    turtle.exitonclick()
