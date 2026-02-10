import re
import random

import gamestate

from moves import apply_move, find_legal_moves
from utils import output_boardstate


def rank_to_row(raw_row, rank):
    """
    Convert a singular row into a row given its rank

    Example: raw_row = 255 (11111111), rank = 2 -> 65280 (1111111100000000)
    """

    return raw_row << (8 * (rank - 1))


def init_bitboards():
    """
    Initialise bitboards for white and black, returning a tuple of the white and black bitboard array, in that order.

    bb1 = pawns, bb2 = rooks, bb3 = knight, bb4 = bishop, bb5 = queen, bb6 = king

    Bottom left of board (a1) is index 0, incrementing from left to right and down to up, until reaching top right (h8)
    """

    pawns_row = 0b11111111
    rooks_row = 0b10000001
    knights_row = 0b01000010
    bishops_row = 0b00100100
    d_file_bit = 0b00001000
    e_file_bit = 0b00010000

    # Create bitboards for white
    bitboards_white = [
        rank_to_row(pawns_row, 2),
        rooks_row,
        knights_row,
        bishops_row,
        d_file_bit,
        e_file_bit,
    ]
    # Create bitboards for black
    bitboards_black = [
        rank_to_row(pawns_row, 7),
        rank_to_row(rooks_row, 8),
        rank_to_row(knights_row, 8),
        rank_to_row(bishops_row, 8),
        rank_to_row(d_file_bit, 8),
        rank_to_row(e_file_bit, 8),
    ]

    return (bitboards_white, bitboards_black)


def user_wants_white():
    """
    Get what colour the user wants to play as
    """

    white_options = ["white", "w"]
    black_options = ["black", "b"]

    while True:
        response = input("Do you want to play as white or black? \n").lower()
        if response in white_options:
            return True
        elif response in black_options:
            return False


def square_to_index(square):
    """
    Convert a square to its board index
    """

    file = square[0]
    rank = int(square[1])

    return ord(file) - 97 + (rank - 1) * 8


def get_move():
    """
    Get users move and convert it to index format

    e.g. Nc3 = b1c3 -> (1, 18)
    """

    while True:
        move = input("Please enter your move: ").lower()

        if re.match("[a-h][1-8][a-h][1-8]", move):
            break

    start_square = move[:2]
    end_square = move[2:]

    return (square_to_index(start_square), square_to_index(end_square))


def get_computer_move(user_bbs, computer_bbs):
    """
    Generate a move for the computer to make
    """

    legal_moves = find_legal_moves(
        computer_bbs,
        user_bbs,
        gamestate.is_whites_move,
        gamestate.castling_rights,
        gamestate.temp_pawn_idx,
        gamestate.real_pawn_idx,
        gamestate.halfmove_clock,
    )

    return random.choice(legal_moves)


def main():
    gamestate.is_playing_white = user_wants_white()
    white_bbs, black_bbs = init_bitboards()

    user_bbs = white_bbs if gamestate.is_playing_white else black_bbs
    computer_bbs = black_bbs if gamestate.is_playing_white else white_bbs

    is_users_move = gamestate.is_playing_white and gamestate.is_whites_move

    while True:
        output_boardstate(user_bbs, computer_bbs)

        user_legal_moves = find_legal_moves(
            user_bbs,
            computer_bbs,
            gamestate.is_whites_move,
            gamestate.castling_rights,
            gamestate.temp_pawn_idx,
            gamestate.real_pawn_idx,
            gamestate.halfmove_clock,
        )

        # Repeat until user enters a valid move
        while is_users_move:
            user_move = get_move()
            is_valid_move = user_move in user_legal_moves

            if is_valid_move:
                (
                    user_bbs,
                    computer_bbs,
                    gamestate.temp_pawn_idx,
                    gamestate.real_pawn_idx,
                    gamestate.halfmove_clock,
                ) = apply_move(
                    user_bbs,
                    computer_bbs,
                    user_move,
                    gamestate.temp_pawn_idx,
                    gamestate.real_pawn_idx,
                    gamestate.halfmove_clock,
                )
                gamestate.is_whites_move = not gamestate.is_whites_move
                is_users_move = False

        computer_move = get_computer_move(user_bbs, computer_bbs)
        (
            computer_bbs,
            user_bbs,
            gamestate.temp_pawn_idx,
            gamestate.real_pawn_idx,
            gamestate.halfmove_clock,
        ) = apply_move(
            computer_bbs,
            user_bbs,
            computer_move,
            gamestate.temp_pawn_idx,
            gamestate.real_pawn_idx,
            gamestate.halfmove_clock,
        )
        gamestate.is_whites_move = not gamestate.is_whites_move
        is_users_move = True


if __name__ == "__main__":
    main()
