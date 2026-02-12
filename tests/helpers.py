import gamestate
from gamestate import (
    is_whites_move,
    is_playing_white,
    castling_rights,
    temp_pawn_idx,
    real_pawn_idx,
    halfmove_clock,
    position_counts,
)


def set_gamestate(
    is_whites_move=True,
    is_playing_white=True,
    castling_rights=15,
    temp_pawn_idx=0,
    real_pawn_idx=0,
    halfmove_clock=0,
    position_counts=None,
):
    """
    Function to set a custom gamestate
    """

    gamestate.is_whites_move = is_whites_move
    gamestate.is_playing_white = is_playing_white
    gamestate.castling_rights = castling_rights
    gamestate.temp_pawn_idx = temp_pawn_idx
    gamestate.real_pawn_idx = real_pawn_idx
    gamestate.halfmove_clock = halfmove_clock
    gamestate.position_counts = {} if position_counts is None else dict(position_counts)


def reset_gamestate():
    """
    Reset gamestate back to defaults
    """

    gamestate.is_whites_move = is_whites_move
    gamestate.is_playing_white = is_playing_white
    gamestate.castling_rights = castling_rights
    gamestate.temp_pawn_idx = temp_pawn_idx
    gamestate.real_pawn_idx = real_pawn_idx
    gamestate.halfmove_clock = halfmove_clock
    gamestate.position_counts = dict(position_counts)


def game_bbs_from_indexes(
    pawn_idxs=None,
    rook_idxs=None,
    knight_idxs=None,
    bishop_idxs=None,
    queen_idxs=None,
    king_idxs=None,
):
    """
    Generate a set of bitboards from tuples of lists of indexes of where each piece should be placed.

    E.g. pawn_idxs = (white pawn indexes, black pawn indexes), white pawn indexes = [8, 9, 10, 11, 12, 13, 14, 15]
    """

    pawn_idxs = ([], []) if pawn_idxs is None else pawn_idxs
    rook_idxs = ([], []) if rook_idxs is None else rook_idxs
    knight_idxs = ([], []) if knight_idxs is None else knight_idxs
    bishop_idxs = ([], []) if bishop_idxs is None else bishop_idxs
    queen_idxs = ([], []) if queen_idxs is None else queen_idxs
    king_idxs = ([], []) if king_idxs is None else king_idxs

    white_p, black_p = pawn_idxs
    white_r, black_r = rook_idxs
    white_n, black_n = knight_idxs
    white_b, black_b = bishop_idxs
    white_q, black_q = queen_idxs
    white_k, black_k = king_idxs

    white_lists = [white_p, white_r, white_n, white_b, white_q, white_k]
    black_lists = [black_p, black_r, black_n, black_b, black_q, black_k]

    white_bbs = []
    for lst in white_lists:
        bb = 0
        for sq in lst:
            bb |= 1 << sq

        white_bbs.append(bb)

    black_bbs = []
    for lst in black_lists:
        bb = 0
        for sq in lst:
            bb |= 1 << sq

        black_bbs.append(bb)

    return (white_bbs, black_bbs)


def init_default_bbs():
    """
    Initialise a default set of bitboards
    """

    return game_bbs_from_indexes(
        ([8, 9, 10, 11, 12, 13, 14, 15], [48, 49, 50, 51, 52, 53, 54, 55]),
        ([0, 7], [56, 63]),
        ([1, 6], [57, 62]),
        ([2, 5], [58, 61]),
        ([3], [59]),
        ([4], [60]),
    )


def pad_move_tuples(moves):
    """
    Converts a list of moves of the form (start_square, end_square) to (start_square, end_square, None)
    """

    return [(m[0], m[1], None) for m in moves]
