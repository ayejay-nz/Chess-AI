import re
import random

import gamestate

from game import draw_by_insufficient_material, game_over_status, update_repetition_count
from moves import apply_move, find_legal_moves
from utils import get_rank, output_boardstate


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


def is_promotion_move(start_idx, end_idx, pawn_bb):
    """
    Check if a user entered move is a promotion move
    """

    start_square = 2**start_idx

    # User is moving a pawn to final rank
    if start_square & pawn_bb:
        rank = get_rank(end_idx)
        return rank == 7 if gamestate.is_playing_white else rank == 0

    return False


def get_move(pawn_bbs):
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

    start_idx = square_to_index(start_square)
    end_idx = square_to_index(end_square)

    promoting = is_promotion_move(start_idx, end_idx, pawn_bbs)
    promotion_piece = None
    while promoting:
        promotion_piece = input(
            "Select a piece to promote to: (q)ueen, (n)knight, (r)ook, (b)ishop: "
        ).lower()
        if promotion_piece in ["q", "n", "r", "b"]:
            break

    return start_idx, end_idx, promotion_piece


def get_computer_move(legal_moves, user_bbs, computer_bbs):
    """
    Generate a move for the computer to make
    """

    # Later evaluate position and pick the best move
    return random.choice(legal_moves)


def apply_real_move(player_bbs, opposition_bbs, move):
    """
    Apply a players move to the bitboards and return the result
    """

    (
        player_bbs,
        opposition_bbs,
        gamestate.temp_pawn_idx,
        gamestate.real_pawn_idx,
        gamestate.halfmove_clock,
        gamestate.castling_rights,
    ) = apply_move(
        player_bbs,
        opposition_bbs,
        move,
        gamestate.temp_pawn_idx,
        gamestate.real_pawn_idx,
        gamestate.halfmove_clock,
        gamestate.castling_rights,
        gamestate.is_whites_move,
    )
    gamestate.is_whites_move = not gamestate.is_whites_move

    if gamestate.halfmove_clock >= 100:
        print("Draw by 50-move rule.")
        return player_bbs, opposition_bbs, True

    return player_bbs, opposition_bbs, False


def output_game_over_message(status):
    """
    Display a simple message after a stalemate or checkmate, depending on who won
    """

    if status == 0:
        print("Draw by stalemate")
    elif status == 1:
        print("User won by checkmate")
    else:
        print("Computer won by checkmate")


def main():
    gamestate.is_playing_white = user_wants_white()
    white_bbs, black_bbs = init_bitboards()

    user_bbs = white_bbs if gamestate.is_playing_white else black_bbs
    computer_bbs = black_bbs if gamestate.is_playing_white else white_bbs

    is_users_move = gamestate.is_playing_white and gamestate.is_whites_move

    while True:
        output_boardstate(user_bbs, computer_bbs)

        if is_users_move:
            player_bbs = user_bbs
            opposition_bbs = computer_bbs
        else:
            player_bbs = computer_bbs
            opposition_bbs = user_bbs

        legal_moves = find_legal_moves(
            player_bbs,
            opposition_bbs,
            gamestate.is_whites_move,
            gamestate.castling_rights,
            gamestate.temp_pawn_idx,
            gamestate.real_pawn_idx,
            gamestate.halfmove_clock,
        )

        # No legal moves to make, so either stalemate or checkmate
        if not legal_moves:
            status = game_over_status(
                player_bbs,
                opposition_bbs,
                is_users_move,
                gamestate.is_whites_move,
                gamestate.castling_rights,
                gamestate.temp_pawn_idx,
            )
            output_game_over_message(status)
            return

        # Check if draw by insufficient material
        if draw_by_insufficient_material(user_bbs, computer_bbs):
            print("Draw by insufficient material")
            return

        # Check if draw by threefold repetition
        white_bbs_ref = user_bbs if gamestate.is_playing_white else computer_bbs
        black_bbs_ref = computer_bbs if gamestate.is_playing_white else user_bbs
        if update_repetition_count(
            white_bbs_ref,
            black_bbs_ref,
            gamestate.is_whites_move,
            gamestate.castling_rights,
            gamestate.temp_pawn_idx,
            legal_moves,
        ):
            print("Draw by threefold repetition")
            return

        if is_users_move:
            # Repeat until user enters a valid move
            while is_users_move:
                user_move = get_move(user_bbs[0])
                is_valid_move = user_move in legal_moves

                if is_valid_move:
                    user_bbs, computer_bbs, game_ended = apply_real_move(
                        user_bbs, computer_bbs, user_move
                    )
                    if game_ended:
                        return

                    is_users_move = False
        else:
            computer_move = get_computer_move(legal_moves, user_bbs, computer_bbs)

            computer_bbs, user_bbs, game_ended = apply_real_move(
                computer_bbs, user_bbs, computer_move
            )
            if game_ended:
                return

            is_users_move = True


if __name__ == "__main__":
    main()
