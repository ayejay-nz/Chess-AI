import numpy as np

BLANK_SQUARE = '.'
BOARDSIZE = 8

FILE_LETTERS = ["a", "b", "c", "d", "e", "f", "g", "h"]

PIECE_SYMBOLS = {
    "r": "♖", "R": "♜",
    "n": "♘", "N": "♞",
    "b": "♗", "B": "♝",
    "q": "♕", "Q": "♛",
    "k": "♔", "K": "♚",
    "p": "♙", "P": "♟",
    ".": "."
}

board = np.array([
    ("r", "n", "b", "q", "k", "b", "n", "r"),
    ("p", "p", "p", "p", "p", "p", "p", "p"),
    (".", ".", ".", ".", ".", ".", ".", "."), 
    (".", ".", ".", ".", ".", ".", ".", "."), 
    (".", ".", ".", ".", ".", ".", ".", "."), 
    (".", ".", ".", ".", ".", ".", ".", "."), 
    ("P", "P", "P", "P", "P", "P", "P", "P"), 
    ("R", "N", "B", "Q", "K", "B", "N", "R")
])

def print_board(board):
    for i, row in enumerate(board):
        print(BOARDSIZE - i, end=' ')
        for square in row:
            print(PIECE_SYMBOLS[square], end='  ')
        print('')

    print('  ', end='')
    for letter in FILE_LETTERS:
        print(letter, end='  ')

print_board(board)