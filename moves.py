import re
import board

def get_move():
    """A simple function that gets the users desired move"""

    move = input("Please enter a move (e.g. a2a3): ")

    return move

def is_valid_move(move):
    """
    A function that checks if the move entered is a valid move.\n
    Checks:
     - If the move is 4 characters long
     - If the format is correct (contains 2 squares on the board)
     - If the first square is one of the users pieces
    """

    if len(move) == 4:
        # Check if move is of the correct format
        correct_format = bool(re.match(r"[a-h][1-8][a-h][1-8]", move))

        return correct_format
    
    return False

def move_to_vector(move):
    """
    A function which converts a move into two vectors\n
     - e.g. a2a3 -> ((0, 1), (0, 2))
    """

    # Split move into start and end square
    start_square = move[:2]
    end_square = move[2:4]

    # Get vector position for start square
    start_file = start_square[0]
    start_file_index = board.FILE_LETTERS.index(start_file)

    start_row = int(start_square[1]) - 1

    start_vector = (start_file_index, start_row)

    # Get vector position for end square
    end_file = end_square[0]
    end_file_index = board.FILE_LETTERS.index(end_file)

    end_row = int(end_square[1]) - 1

    end_vector = (end_file_index, end_row)

    return (start_vector, end_vector)