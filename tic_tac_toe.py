import tkinter as tk
from tkinter import messagebox

# Modern Color Palette
BG_DARK = "#121212"
CARD_BG = "#1e1e1e"
TEXT_X = "#00ffcc"       # Neon Cyan
TEXT_O = "#ff007f"       # Neon Pink
WIN_BG = "#2ecc71"
HOVER_BG = "#2a2a2a"

# Global Variables
current_player = "X"
scores = {"X": 0, "O": 0}

def check_winner():
    combos = [[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]]
    for combo in combos:
        if buttons[combo[0]]["text"] == buttons[combo[1]]["text"] == buttons[combo[2]]["text"] != "":
            winner = buttons[combo[0]]["text"]
            for i in combo:
                buttons[i].config(bg=WIN_BG, fg="white")
            
            # Update Score
            scores[winner] += 1
            score_label.config(text=f"X: {scores['X']}  |  O: {scores['O']}")
            
            messagebox.showinfo("VICTORY", f"Player {winner} is the champion!")
            reset_board()
            return True

    if all(b["text"] != "" for b in buttons):
        messagebox.showinfo("TIE", "It's a draw! 🤝")
        reset_board()
        return True
    return False

def b_click(index):
    global current_player # Added global keyword to fix NameError
    if buttons[index]["text"] == "":
        color = TEXT_X if current_player == "X" else TEXT_O
        buttons[index].config(text=current_player, fg=color)
        if not check_winner():
            toggle_player()

def toggle_player():
    global current_player # Added global keyword
    current_player = "O" if current_player == "X" else "X"
    color = TEXT_X if current_player == "X" else TEXT_O
    turn_label.config(text=f"TURN: PLAYER {current_player}", fg=color)

def reset_board():
    global current_player
    current_player = "X"
    for b in buttons:
        b.config(text="", bg=CARD_BG, fg="white")
    turn_label.config(text=f"TURN: PLAYER {current_player}", fg=TEXT_X)

# --- UI Setup ---
root = tk.Tk()
root.title("Tic-Tac-Toe Ultra")
root.geometry("400x600")
root.configure(bg=BG_DARK)

# Turn Indicator
turn_label = tk.Label(root, text="TURN: PLAYER X", font=("Impact", 20), 
                 bg=BG_DARK, fg=TEXT_X, pady=15)
turn_label.pack()

# Score Board
score_label = tk.Label(root, text="X: 0  |  O: 0", font=("Consolas", 14, "bold"),
                  bg=BG_DARK, fg="#888888")
score_label.pack()

# Game Grid Container
grid_frame = tk.Frame(root, bg=BG_DARK)
grid_frame.pack(pady=15)

buttons = []
for i in range(9):
    btn = tk.Button(grid_frame, text="", font=("Impact", 32), width=4, height=1,
                    bg=CARD_BG, fg="white", bd=0, cursor="hand2",
                    activebackground=HOVER_BG, activeforeground="white",
                    command=lambda i=i: b_click(i))
    btn.grid(row=i // 3, column=i % 3, padx=6, pady=6)
    
    # Hover Effects
    btn.bind("<Enter>", lambda e, b=btn: b.config(bg=HOVER_BG) if b["text"] == "" else None)
    btn.bind("<Leave>", lambda e, b=btn: b.config(bg=CARD_BG) if b["text"] == "" else None)
    buttons.append(btn)

# Modern Restart Button
restart_btn = tk.Button(root, text="NEW GAME", font=("Arial", 12, "bold"),
                        bg="#333333", fg="white", bd=0, padx=30, pady=12,
                        activebackground="#444444", cursor="hand2",
                        command=reset_board)
restart_btn.pack(pady=20)

root.mainloop()

