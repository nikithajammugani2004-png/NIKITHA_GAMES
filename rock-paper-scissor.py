"""
WORKING OF GAME:
    1. input from user(rock(R), paper(p), scissor(S))
    2. computer choice (computer will choose randomly not conditionally)
    3. print the results

Cases:
A --> R
    R - R : TIE
    R - P : P WINS
    R - S : R WINS

B --> P
    P - P : TIE
    P - R : P WINS
    S - P : S WINS

C --> S
    S - S : TIE
    S - R : R WINS
    S - P : S WINS
"""

import tkinter as tk
import random
from tkinter import messagebox

class RPSGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Rock Paper Scissors - Visual Edition")
        self.root.geometry("400x500")
        self.root.configure(bg="#2c3e50")

        # Game Logic Variables
        self.user_score = 0
        self.comp_score = 0
        self.choices = {'R': '🪨', 'P': '📄', 'S': '✂️'}
        self.names = {'R': 'Rock', 'P': 'Paper', 'S': 'Scissors'}

        self.setup_ui()

    def setup_ui(self):
        # Score Header
        self.score_label = tk.Label(self.root, text="You: 0  |  CPU: 0", font=("Arial", 18, "bold"), 
                                    fg="#ecf0f1", bg="#2c3e50", pady=20)
        self.score_label.pack()

        # Display Area
        self.display_frame = tk.Frame(self.root, bg="#34495e", padx=20, pady=20)
        self.display_frame.pack(pady=10)

        self.user_display = tk.Label(self.display_frame, text="👤\nReady", font=("Arial", 30), bg="#34495e", fg="white")
        self.user_display.grid(row=0, column=0, padx=20)

        self.vs_label = tk.Label(self.display_frame, text="VS", font=("Arial", 20, "bold"), bg="#34495e", fg="#e74c3c")
        self.vs_label.grid(row=0, column=1)

        self.comp_display = tk.Label(self.display_frame, text="🤖\nReady", font=("Arial", 30), bg="#34495e", fg="white")
        self.comp_display.grid(row=0, column=2, padx=20)

        # Result Message
        self.result_label = tk.Label(self.root, text="Pick your move!", font=("Arial", 14), 
                                     fg="#f1c40f", bg="#2c3e50", pady=20)
        self.result_label.pack()

        # Buttons Frame
        btn_frame = tk.Frame(self.root, bg="#2c3e50")
        btn_frame.pack(pady=10)

        for key, icon in self.choices.items():
            btn = tk.Button(btn_frame, text=f"{icon}\n{self.names[key]}", font=("Arial", 12, "bold"),
                            width=8, height=3, command=lambda k=key: self.play(k),
                            bg="#ecf0f1", activebackground="#bdc3c7")
            btn.pack(side=tk.LEFT, padx=10)

        # Reset Button
        tk.Button(self.root, text="Reset Game", command=self.reset_game, bg="#e74c3c", fg="white").pack(side="bottom", pady=20)

    def play(self, user_move):
        comp_move = random.choice(['R', 'P', 'S'])
        
        # Update Visuals
        self.user_display.config(text=f"👤\n{self.choices[user_move]}")
        self.comp_display.config(text=f"🤖\n{self.choices[comp_move]}")

        # Game Logic
        if user_move == comp_move:
            res = "It's a Tie! 🤝"
        elif (user_move == 'R' and comp_move == 'S') or \
             (user_move == 'P' and comp_move == 'R') or \
             (user_move == 'S' and comp_move == 'P'):
            res = f"You Win! 🎉\n{self.names[user_move]} beats {self.names[comp_move]}"
            self.user_score += 1
        else:
            res = f"Computer Wins! 🤖\n{self.names[comp_move]} beats {self.names[user_move]}"
            self.comp_score += 1

        # Update Score and Result
        self.result_label.config(text=res)
        self.score_label.config(text=f"You: {self.user_score}  |  CPU: {self.comp_score}")

    def reset_game(self):
        self.user_score = 0
        self.comp_score = 0
        self.score_label.config(text="You: 0  |  CPU: 0")
        self.result_label.config(text="Pick your move!")
        self.user_display.config(text="👤\nReady")
        self.comp_display.config(text="🤖\nReady")

if __name__ == "__main__":
    root = tk.Tk()
    game = RPSGame(root)
    root.mainloop()
