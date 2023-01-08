import re
import board

def get_move():
    """A simple function that gets the users desired move"""

    move = input("Please enter a move (e.g. a2a3): ")

    return move

def is_correct_format(move):
    """
    A function that checks if the move entered is in the correct format.\n
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
     - e.g. a2a3 -> ((6, 0), (5, 0))
     - NOTE: Vectors are of the form (y, x) due to the nature of the arrays being used.
     I know it sucks but this is by far the easiest solution.
     - NOTE: The origin, (0, 0), of the board is the square a8 also due do the nature of the arrays.
    """

    # Split move into start and end square
    start_square = move[:2]
    end_square = move[2:4]

    # Get vector position for start square
    start_file = start_square[0]
    start_file_index = board.FILE_LETTERS.index(start_file)

    start_row = board.BOARDSIZE - int(start_square[1])

    start_vector = (start_row, start_file_index)

    # Get vector position for end square
    end_file = end_square[0]
    end_file_index = board.FILE_LETTERS.index(end_file)

    end_row = board.BOARDSIZE - int(end_square[1])

    end_vector = (end_row, end_file_index)

    return (start_vector, end_vector)

def move_vector(start_vector, end_vector):
    """
    A function which calculates the vector of the move
     - e.g. a2a3 -> (-1, 0)
    """

    # Calculate the net vector along the file axis
    file_distance = end_vector[0] - start_vector[0]

    # Calculate the net vector along the row axis
    row_distance =  end_vector[1] - start_vector[1]

    vector = (file_distance, row_distance)

    return vector

def contains_own_piece(square_vector, whites_move):
    """A function that checks if a square contains the current players piece"""
    
    piece = board.chessboard([square_vector])
    
    if whites_move: 
        # Check if piece is upper case (a white piece)
        return piece == piece.upper()
    else:
        # Check if piece is lower case (a black piece)
        return piece == piece.lower()
        
def is_blank_square(square_vector):
    """A function that checks if a square is blank"""

    if board.chessboard[square_vector] == board.BLANK_SQUARE:
        return True

    return False

def is_end_square_valid(end_vector, whites_move):
    """A function that checks if the end square is blank or contains an enemy piece"""

    # Check if end square is blank
    if is_blank_square(end_vector):
        return True

    # Check if end square has enemy piece
    return not contains_own_piece(end_vector, whites_move)

