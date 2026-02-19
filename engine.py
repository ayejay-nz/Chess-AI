import math
import time

from game import draw_by_insufficient_material, set_position_count
from moves import apply_move, find_legal_moves, find_pseudo_legal_moves, in_check

CHECKMATE_VALUE = 32000

MG_VALUES = {
    0: 82,  # pawn
    1: 477,  # rook
    2: 337,  # knight
    3: 365,  # bishop
    4: 1025,  # queen
}
EG_VALUES = {
    0: 94,  # pawn
    1: 512,  # rook
    2: 281,  # knight
    3: 197,  # bishop
    4: 936,  # queen
}


# fmt: off
mg_pawn_table = [
      0,   0,   0,   0,   0,   0,  0,   0,
     98, 134,  61,  95,  68, 126, 34, -11,
     -6,   7,  26,  31,  65,  56, 25, -20,
    -14,  13,   6,  21,  23,  12, 17, -23,
    -27,  -2,  -5,  12,  17,   6, 10, -25,
    -26,  -4,  -4, -10,   3,   3, 33, -12,
    -35,  -1, -20, -23, -15,  24, 38, -22,
      0,   0,   0,   0,   0,   0,  0,   0,
]
eg_pawn_table = [
      0,   0,   0,   0,   0,   0,   0,   0,
    178, 173, 158, 134, 147, 132, 165, 187,
     94, 100,  85,  67,  56,  53,  82,  84,
     32,  24,  13,   5,  -2,   4,  17,  17,
     13,   9,  -3,  -7,  -7,  -8,   3,  -1,
      4,   7,  -6,   1,   0,  -5,  -1,  -8,
     13,   8,   8,  10,  13,   0,   2,  -7,
      0,   0,   0,   0,   0,   0,   0,   0,
]
mg_knight_table = [
    -167, -89, -34, -49,  61, -97, -15, -107,
     -73, -41,  72,  36,  23,  62,   7,  -17,
     -47,  60,  37,  65,  84, 129,  73,   44,
      -9,  17,  19,  53,  37,  69,  18,   22,
     -13,   4,  16,  13,  28,  19,  21,   -8,
     -23,  -9,  12,  10,  19,  17,  25,  -16,
     -29, -53, -12,  -3,  -1,  18, -14,  -19,
    -105, -21, -58, -33, -17, -28, -19,  -23,
]
eg_knight_table = [
    -58, -38, -13, -28, -31, -27, -63, -99,
    -25,  -8, -25,  -2,  -9, -25, -24, -52,
    -24, -20,  10,   9,  -1,  -9, -19, -41,
    -17,   3,  22,  22,  22,  11,   8, -18,
    -18,  -6,  16,  25,  16,  17,   4, -18,
    -23,  -3,  -1,  15,  10,  -3, -20, -22,
    -42, -20, -10,  -5,  -2, -20, -23, -44,
    -29, -51, -23, -15, -22, -18, -50, -64,
]
mg_bishop_table = [
    -29,   4, -82, -37, -25, -42,   7,  -8,
    -26,  16, -18, -13,  30,  59,  18, -47,
    -16,  37,  43,  40,  35,  50,  37,  -2,
     -4,   5,  19,  50,  37,  37,   7,  -2,
     -6,  13,  13,  26,  34,  12,  10,   4,
      0,  15,  15,  15,  14,  27,  18,  10,
      4,  15,  16,   0,   7,  21,  33,   1,
    -33,  -3, -14, -21, -13, -12, -39, -21,
]
eg_bishop_table = [
    -14, -21, -11,  -8, -7,  -9, -17, -24,
     -8,  -4,   7, -12, -3, -13,  -4, -14,
      2,  -8,   0,  -1, -2,   6,   0,   4,
     -3,   9,  12,   9, 14,  10,   3,   2,
     -6,   3,  13,  19,  7,  10,  -3,  -9,
    -12,  -3,   8,  10, 13,   3,  -7, -15,
    -14, -18,  -7,  -1,  4,  -9, -15, -27,
    -23,  -9, -23,  -5, -9, -16,  -5, -17,
]
mg_rook_table = [
     32,  42,  32,  51, 63,  9,  31,  43,
     27,  32,  58,  62, 80, 67,  26,  44,
     -5,  19,  26,  36, 17, 45,  61,  16,
    -24, -11,   7,  26, 24, 35,  -8, -20,
    -36, -26, -12,  -1,  9, -7,   6, -23,
    -45, -25, -16, -17,  3,  0,  -5, -33,
    -44, -16, -20,  -9, -1, 11,  -6, -71,
    -19, -13,   1,  17, 16,  7, -37, -26,
]
eg_rook_table = [
    13, 10, 18, 15, 12,  12,   8,   5,
    11, 13, 13, 11, -3,   3,   8,   3,
     7,  7,  7,  5,  4,  -3,  -5,  -3,
     4,  3, 13,  1,  2,   1,  -1,   2,
     3,  5,  8,  4, -5,  -6,  -8, -11,
    -4,  0, -5, -1, -7, -12,  -8, -16,
    -6, -6,  0,  2, -9,  -9, -11,  -3,
    -9,  2,  3, -1, -5, -13,   4, -20,
]
mg_queen_table = [
    -28,   0,  29,  12,  59,  44,  43,  45,
    -24, -39,  -5,   1, -16,  57,  28,  54,
    -13, -17,   7,   8,  29,  56,  47,  57,
    -27, -27, -16, -16,  -1,  17,  -2,   1,
     -9, -26,  -9, -10,  -2,  -4,   3,  -3,
    -14,   2, -11,  -2,  -5,   2,  14,   5,
    -35,  -8,  11,   2,   8,  15,  -3,   1,
     -1, -18,  -9,  10, -15, -25, -31, -50,
]
eg_queen_table = [
     -9,  22,  22,  27,  27,  19,  10,  20,
    -17,  20,  32,  41,  58,  25,  30,   0,
    -20,   6,   9,  49,  47,  35,  19,   9,
      3,  22,  24,  45,  57,  40,  57,  36,
    -18,  28,  19,  47,  31,  34,  39,  23,
    -16, -27,  15,   6,   9,  17,  10,   5,
    -22, -23, -30, -16, -16, -23, -36, -32,
    -33, -28, -22, -43,  -5, -32, -20, -41,
]
mg_king_table = [
    -65,  23,  16, -15, -56, -34,   2,  13,
     29,  -1, -20,  -7,  -8,  -4, -38, -29,
     -9,  24,   2, -16, -20,   6,  22, -22,
    -17, -20, -12, -27, -30, -25, -14, -36,
    -49,  -1, -27, -39, -46, -44, -33, -51,
    -14, -14, -22, -46, -44, -30, -15, -27,
      1,   7,  -8, -64, -43, -16,   9,   8,
    -15,  36,  12, -54,   8, -28,  24,  14,
]
eg_king_table = [
    -74, -35, -18, -18, -11,  15,   4, -17,
    -12,  17,  14,  17,  17,  38,  23,  11,
     10,  17,  23,  15,  20,  45,  44,  13,
     -8,  22,  24,  27,  26,  33,  26,   3,
    -18,  -4,  21,  24,  27,  23,   9, -11,
    -19,  -3,  11,  21,  23,  16,   7,  -9,
    -27, -11,   4,  13,  14,   4,  -5, -17,
    -53, -34, -21, -11, -28, -14, -24, -43,
]
# fmt: on


mg_bbs = [
    mg_pawn_table,
    mg_rook_table,
    mg_knight_table,
    mg_bishop_table,
    mg_queen_table,
    mg_king_table,
]
eg_bbs = [
    eg_pawn_table,
    eg_rook_table,
    eg_knight_table,
    eg_bishop_table,
    eg_queen_table,
    eg_king_table,
]


phase_inc = {
    0: 0,  # pawn
    1: 2,  # rook
    2: 1,  # knight
    3: 1,  # bishop
    4: 4,  # queen
}


def pesto_evaluation(white_bbs, black_bbs):
    """
    Evaluate the current position using opening/middlegame and endgame piece-square tables,
    interpolating between the two based on the remaining material
    """

    mg_eval = 0
    eg_eval = 0
    game_phase = 0

    for idx, bb in enumerate(white_bbs):
        while bb:
            lsb = bb & -bb
            square = (lsb.bit_length() - 1) ^ 56

            mg_eval += mg_bbs[idx][square] + MG_VALUES.get(idx, 0)
            eg_eval += eg_bbs[idx][square] + EG_VALUES.get(idx, 0)
            game_phase += phase_inc.get(idx, 0)

            bb ^= lsb

    for idx, bb in enumerate(black_bbs):
        while bb:
            lsb = bb & -bb
            square = lsb.bit_length() - 1

            mg_eval -= mg_bbs[idx][square] + MG_VALUES.get(idx, 0)
            eg_eval -= eg_bbs[idx][square] + EG_VALUES.get(idx, 0)
            game_phase += phase_inc.get(idx, 0)

            bb ^= lsb

    # tapered eval
    mg_phase = game_phase
    if mg_phase > 24:
        mg_phase = 24  # in case of early promotion
    eg_phase = 24 - mg_phase

    return (mg_eval * mg_phase + eg_eval * eg_phase) / 24


def static_eval(player_bbs, opposition_bbs, is_whites_move):
    """
    Return an evaluation relative to the player provided
    """

    white_bbs = player_bbs if is_whites_move else opposition_bbs
    black_bbs = opposition_bbs if is_whites_move else player_bbs
    score_white_pov = pesto_evaluation(white_bbs, black_bbs)

    return score_white_pov if is_whites_move else -score_white_pov


def negamax(
    player_bbs,
    opposition_bbs,
    is_whites_move,
    castling_rights,
    en_passant_temp_idx,
    en_passant_real_idx,
    halfmove_clock,
    alpha,
    beta,
    ply=0,
    depth=3,
    deadline=None,
):
    """
    Negamax search algorithm for the provided position to the desired depth
    """

    if deadline is not None and time.monotonic() >= deadline:
        return static_eval(player_bbs, opposition_bbs, is_whites_move), ()

    if draw_by_insufficient_material(player_bbs, opposition_bbs):
        return 0, ()

    # Draw by 50-move rule
    if halfmove_clock >= 100:
        return 0, ()

    legal_moves = find_legal_moves(
        player_bbs,
        opposition_bbs,
        is_whites_move,
        castling_rights,
        en_passant_temp_idx,
        en_passant_real_idx,
        halfmove_clock,
    )

    # No legal moves, so a mate has occurred
    if not legal_moves:
        king_square = player_bbs[5].bit_length() - 1
        o_piece_captures, o_king_moves, _, _ = find_pseudo_legal_moves(
            opposition_bbs, player_bbs, not is_whites_move, castling_rights, en_passant_temp_idx
        )

        if in_check(king_square, o_piece_captures + o_king_moves):
            return -CHECKMATE_VALUE + ply, ()

        return 0, ()  # stalemate

    if depth == 0:
        return static_eval(player_bbs, opposition_bbs, is_whites_move), ()

    best_move = ()
    best_score = -math.inf

    for move in legal_moves:
        (
            new_player_bbs,
            new_opposition_bbs,
            new_en_passant_temp_idx,
            new_en_passant_real_idx,
            new_halfmove_clock,
            new_castling_rights,
        ) = apply_move(
            player_bbs,
            opposition_bbs,
            move,
            en_passant_temp_idx,
            en_passant_real_idx,
            halfmove_clock,
            castling_rights,
            is_whites_move,
        )

        child_score, _ = negamax(
            new_opposition_bbs,
            new_player_bbs,
            not is_whites_move,
            new_castling_rights,
            new_en_passant_temp_idx,
            new_en_passant_real_idx,
            new_halfmove_clock,
            -beta,
            -alpha,
            ply + 1,
            depth - 1,
            deadline,
        )
        score = -child_score

        if score > best_score:
            best_score = score
            best_move = move

            if (score > alpha):
                alpha = score

        if (score >= beta):
            break

    return best_score, best_move


def evaluate_position(
    white_bbs,
    black_bbs,
    is_whites_move,
    en_passant_temp_idx,
    en_passant_real_idx,
    castling_rights,
    halfmove_clock,
    depth=3,
    deadline=None,
):
    """
    Returns an evaluation of the the specified board position from the
    point of view of white, as well as the best move
    """

    player_bbs = white_bbs if is_whites_move else black_bbs
    opposition_bbs = black_bbs if is_whites_move else white_bbs

    best_eval, best_move = negamax(
        player_bbs,
        opposition_bbs,
        is_whites_move,
        castling_rights,
        en_passant_temp_idx,
        en_passant_real_idx,
        halfmove_clock,
        alpha=-math.inf,
        beta=math.inf,
        depth=depth,
        deadline=deadline,
    )
    true_eval = best_eval if is_whites_move else -best_eval

    return true_eval, best_move
