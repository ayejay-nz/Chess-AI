import math
import time
from contextlib import nullcontext
from dataclasses import dataclass

from book import probe_opening_book
from game import draw_by_insufficient_material
from moves import apply_move, find_legal_moves, is_square_attacked
from profiler import active_profiler
from zobrist import compute_polyglot_key

EXACT, LOWER, UPPER = 0, 1, 2


@dataclass
class TTEntry:
    key: int
    best_move: tuple
    depth: int
    score: int
    node_type: int
    age: int


TT = {}


CHECKMATE_VALUE = 32000

MG_VALUES = {
    0: 82,  # pawn
    1: 337,  # knight
    2: 365,  # bishop
    3: 477,  # rook
    4: 1025,  # queen
}
EG_VALUES = {
    0: 94,  # pawn
    1: 281,  # knight
    2: 197,  # bishop
    3: 512,  # rook
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
    mg_knight_table,
    mg_bishop_table,
    mg_rook_table,
    mg_queen_table,
    mg_king_table,
]
eg_bbs = [
    eg_pawn_table,
    eg_knight_table,
    eg_bishop_table,
    eg_rook_table,
    eg_queen_table,
    eg_king_table,
]


phase_inc = {
    0: 0,  # pawn
    1: 1,  # knight
    2: 1,  # bishop
    3: 2,  # rook
    4: 4,  # queen
}


MVV_LVV = [
    [16, 15, 14, 13, 12, 11, 10],  # victim P, attacker P, N, B, R, Q, K
    [26, 25, 24, 23, 22, 21, 20],  # victim N, attacker P, N, B, R, Q, K
    [36, 35, 34, 33, 32, 31, 30],  # victim B, attacker P, N, B, R, Q, K
    [46, 45, 44, 43, 42, 41, 40],  # victim R, attacker P, N, B, R, Q, K
    [56, 55, 54, 53, 52, 51, 50],  # victim Q, attacker P, N, B, R, Q, K
]


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


def mvv_lva_ordering(legal_moves, player_bbs, opposition_bbs, en_passant_temp_idx):
    """
    Sort the legal moves according to the MVV-LVA heuristic:
    - Lookup potential victims of all attacked opponent pieces, most valuable being first
    - After most valuable is found, find potential aggressors in inverse order (least valuable first)
    """

    def _is_player_pawn(square):
        return bool((1 << square) & player_bbs[0])

    def _find_bb_idx(square, bbs, end_square=False):
        for idx, bb in enumerate(bbs):
            if (1 << square) & bb:
                return idx
            # En passant is the only capture move which can attack the en passant square
            elif end_square and square == en_passant_temp_idx:
                return 0

        return None

    def _find_move_mvv_lva_score(capture_move):
        victim_square = capture_move[1]
        aggressor_square = capture_move[0]

        victim_idx = _find_bb_idx(victim_square, opposition_bbs, True)
        aggressor_idx = _find_bb_idx(aggressor_square, player_bbs)

        return MVV_LVV[victim_idx][aggressor_idx]

    capture_moves = []
    non_capture_moves = []

    occupied_opposition = (
        opposition_bbs[0]
        | opposition_bbs[1]
        | opposition_bbs[2]
        | opposition_bbs[3]
        | opposition_bbs[4]
        | opposition_bbs[5]
    )

    # Find all legal capturing moves
    for move in legal_moves:
        start_square, end_square, _ = move
        # Capturing an opponent piece
        if (1 << end_square) & occupied_opposition:
            capture_moves.append(move)
        elif _is_player_pawn(start_square) and end_square == en_passant_temp_idx:
            capture_moves.append(move)
        else:
            non_capture_moves.append(move)

    # No legal capture moves
    if not capture_moves:
        return non_capture_moves

    # Sort capturing moves according to MVV-LVA
    capture_moves.sort(key=lambda move: _find_move_mvv_lva_score(move), reverse=True)

    return capture_moves + non_capture_moves


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
    zkey,
    ply=0,
    depth=3,
    pv_move=None,
    deadline=None,
):
    """
    Negamax search algorithm for the provided position to the desired depth
    """

    def _search_child(move):
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

        child_white_bbs = new_opposition_bbs if is_whites_move else new_player_bbs
        child_black_bbs = new_player_bbs if is_whites_move else new_opposition_bbs
        child_key = compute_polyglot_key(
            child_white_bbs,
            child_black_bbs,
            new_castling_rights,
            new_en_passant_temp_idx,
            not is_whites_move,
        )

        child_score, _, completed = negamax(
            new_opposition_bbs,
            new_player_bbs,
            not is_whites_move,
            new_castling_rights,
            new_en_passant_temp_idx,
            new_en_passant_real_idx,
            new_halfmove_clock,
            -beta,
            -alpha,
            child_key,
            ply + 1,
            depth - 1,
            None,
            deadline,
        )

        if not completed:
            return 0, False

        return -child_score, True

    def _is_mate_score(s):
        return abs(s) >= CHECKMATE_VALUE - 1000

    def _store_tt(score, move, node_type):
        old = TT.get(zkey)
        if old is None or depth >= old.depth:
            # Normalise mating ply depth
            tt_score = score
            if _is_mate_score(tt_score):
                tt_score = tt_score + ply if tt_score > 0 else tt_score - ply

            TT[zkey] = TTEntry(zkey, move, depth, tt_score, node_type, halfmove_clock)

    if deadline is not None and time.monotonic() >= deadline:
        return 0, (), False

    if draw_by_insufficient_material(player_bbs, opposition_bbs):
        return 0, (), True

    # Draw by 50-move rule
    if halfmove_clock >= 100:
        return 0, (), True

    alpha_orig = alpha
    beta_orig = beta

    # Check transposition table
    entry = TT.get(zkey)
    if entry is not None and entry.depth >= depth:
        # Keep mate distance consistent across different depths
        score = entry.score
        if _is_mate_score(score):
            score = score - ply if score > 0 else score + ply

        if entry.node_type == EXACT:
            return score, entry.best_move, True
        if entry.node_type == LOWER:
            alpha = max(alpha, score)
        if entry.node_type == UPPER:
            beta = min(beta, score)
        if alpha >= beta:
            return score, entry.best_move, True

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
        if is_square_attacked(king_square, opposition_bbs, player_bbs, not is_whites_move):
            return -CHECKMATE_VALUE + ply, (), True

        return 0, (), True  # stalemate

    if depth == 0:
        return static_eval(player_bbs, opposition_bbs, is_whites_move), (), True

    best_move = ()
    best_score = -math.inf

    # Search previous best move first
    if pv_move and pv_move in legal_moves:
        score, completed = _search_child(pv_move)
        if not completed:
            return best_score, best_move, False

        if score > best_score:
            best_score = score
            best_move = pv_move

            if score > alpha:
                alpha = score

        if score >= beta:
            _store_tt(best_score, best_move, LOWER)
            return best_score, best_move, True

    # Apply MVV-LVA move ordering
    ordered_moves = mvv_lva_ordering(legal_moves, player_bbs, opposition_bbs, en_passant_temp_idx)
    for move in ordered_moves:
        if move == pv_move:
            continue

        score, completed = _search_child(move)
        if not completed:
            return best_score, best_move, False

        if score > best_score:
            best_score = score
            best_move = move

            if score > alpha:
                alpha = score

        if score >= beta:
            break

    # Set values for transposition table
    if best_score <= alpha_orig:
        node_type = UPPER
    elif best_score >= beta_orig:
        node_type = LOWER
    else:
        node_type = EXACT

    _store_tt(best_score, best_move, node_type)

    return best_score, best_move, True


def evaluate_position(
    white_bbs,
    black_bbs,
    is_whites_move,
    en_passant_temp_idx,
    en_passant_real_idx,
    castling_rights,
    halfmove_clock,
    depth=10,
    deadline=None,
    profiler=None,
):
    """
    Returns an evaluation of the the specified board position from the
    point of view of white, as well as the best move
    """

    player_bbs = white_bbs if is_whites_move else black_bbs
    opposition_bbs = black_bbs if is_whites_move else white_bbs

    best_move = ()
    best_eval = 0

    # Probe opening book for optimal move
    book_move = probe_opening_book(
        white_bbs, black_bbs, castling_rights, en_passant_temp_idx, is_whites_move
    )
    if book_move:
        legal_moves = find_legal_moves(
            player_bbs,
            opposition_bbs,
            is_whites_move,
            castling_rights,
            en_passant_temp_idx,
            en_passant_real_idx,
            halfmove_clock,
        )
        if book_move in legal_moves:
            return 0, book_move

    # Compute zobrist key for current position
    zkey = compute_polyglot_key(
        white_bbs, black_bbs, castling_rights, en_passant_temp_idx, is_whites_move
    )

    for d in range(1, depth + 1):
        if deadline and time.monotonic() >= deadline:
            break

        profiler_context = active_profiler(profiler) if profiler is not None else nullcontext()
        with profiler_context:
            eval_d, move_d, completed_d = negamax(
                player_bbs,
                opposition_bbs,
                is_whites_move,
                castling_rights,
                en_passant_temp_idx,
                en_passant_real_idx,
                halfmove_clock,
                alpha=-math.inf,
                beta=math.inf,
                zkey=zkey,
                depth=d,
                pv_move=best_move,
                deadline=deadline,
            )

        if not completed_d:
            break

        if move_d:
            best_eval, best_move = eval_d, move_d
        else:
            break

    true_eval = best_eval if is_whites_move else -best_eval
    return true_eval, best_move
