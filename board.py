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

chessboard = np.array([
    ("r", "n", "b", "q", "k", "b", "n", "r"),
    ("p", "p", "p", "p", "p", "p", "p", "p"),
    (".", ".", ".", ".", ".", ".", ".", "."), 
    (".", ".", ".", ".", ".", ".", ".", "."), 
    (".", ".", ".", ".", ".", ".", ".", "."), 
    (".", ".", ".", ".", ".", ".", ".", "."), 
    ("P", "P", "P", "P", "P", "P", "P", "P"), 
    ("R", "N", "B", "Q", "K", "B", "N", "R")
])

def print_chessboard(chessboard):
    for i, row in enumerate(chessboard):
        print(BOARDSIZE - i, end=' ')
        for square in row:
            print(PIECE_SYMBOLS[square], end='  ')
        print('')

    print('  ', end='')
    for letter in FILE_LETTERS:
        print(letter, end='  ')

if __name__ == '__main__':
    print_chessboard(chessboard)