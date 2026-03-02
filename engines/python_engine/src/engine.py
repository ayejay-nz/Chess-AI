import math
import time
from contextlib import nullcontext
from dataclasses import dataclass

from book import probe_opening_book
from evaluation import static_eval
from game import draw_by_insufficient_material
from profiler import active_profiler, bump_node, profiled
from moves import (
    SearchState,
    apply_move,
    find_legal_moves,
    is_square_attacked,
    make_move_inplace,
    move_gives_check,
    unmake_move_inplace,
)
from zobrist import ZobristState, compute_polyglot_key, update_key

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


MAX_PLY = 256
KILLER_MOVES = [[None, None] for _ in range(MAX_PLY)]


MAX_HISTORY = 16384
HISTORY = [[[0]*64 for _ in range(64)] for _ in range(2)] # side, from, to


CHECKMATE_VALUE = 32000


MVV_LVV = [
    [16, 15, 14, 13, 12, 11, 10],  # victim P, attacker P, N, B, R, Q, K
    [26, 25, 24, 23, 22, 21, 20],  # victim N, attacker P, N, B, R, Q, K
    [36, 35, 34, 33, 32, 31, 30],  # victim B, attacker P, N, B, R, Q, K
    [46, 45, 44, 43, 42, 41, 40],  # victim R, attacker P, N, B, R, Q, K
    [56, 55, 54, 53, 52, 51, 50],  # victim Q, attacker P, N, B, R, Q, K
]


def clear_tt():
    TT.clear()


def store_killer_move(ply, move):
    """
    Store a killer move at a specific ply, each ply having a maximum of two killer moves, both unique
    """

    if ply >= MAX_PLY:
        return

    # Insert killer move, ensuring it is unique at the ply level
    if KILLER_MOVES[ply][0] != move:
        KILLER_MOVES[ply][1] = KILLER_MOVES[ply][0]
        KILLER_MOVES[ply][0] = move


# @profiled()
def mvv_lva_ordering(legal_moves, player_bbs, opposition_bbs, en_passant_temp_idx):
    """
    Sort the legal moves according to the MVV-LVA heuristic:
    - Lookup potential victims of all attacked opponent pieces, most valuable being first
    - After most valuable is found, find potential aggressors in inverse order (least valuable first)

    Returns two arrays:
    - First array is the ordered array of attacking moves
    - Second array is the unordered non-capturing moves
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
        return capture_moves, non_capture_moves

    # Sort capturing moves according to MVV-LVA
    capture_moves.sort(key=lambda move: _find_move_mvv_lva_score(move), reverse=True)

    return capture_moves, non_capture_moves


def decay_history():
    """
    Decay previously added history values
    """

    for s in range(2):
        for frm in range(64):
            row = HISTORY[s][frm]
            for to in range(64):
                row[to] //= 2


def clear_history():
    """
    Clear all history heuristic weights
    """

    for s in range(2):
        for frm in range(64):
            row = HISTORY[s][frm]
            for to in range(64):
                row[to] = 0


def history_side_idx(is_whites_move):
    """
    Get history side index for history heuristic
    """

    return 0 if is_whites_move else 1


def add_history(move, depth, side_idx):
    frm, to, _ = move
    bonus = depth * depth
    weight = HISTORY[side_idx][frm][to] + bonus
    HISTORY[side_idx][frm][to] = min(weight, MAX_HISTORY)


def order_moves(
    legal_moves,
    player_bbs,
    opposition_bbs,
    en_passant_temp_idx,
    pv_move,
    tt_entry,
    side_idx,
    ply,
):
    """
    Orders all legal moves in the order they should be searched:
    1. PV move
    2. TT move (if distinct)
    3. Capture moves, ordered by MVV-LVA
    4. Killer moves
    5. History moves
    6. Remaining

    Returns two arrays:
    - An array of tuples (move, is_quite_move boolean)
    - An array of all capture moves
    """

    ordered_moves = []

    if pv_move in legal_moves:
        ordered_moves.append((pv_move, False))  # set this as False for now
        legal_moves.remove(pv_move)

    tt_move = None if tt_entry is None else tt_entry.best_move
    if tt_move is not None and tt_move in legal_moves:
        ordered_moves.append((tt_move, False))  # set this as False for now
        legal_moves.remove(tt_move)

    capture_moves, non_capture_moves = mvv_lva_ordering(
        legal_moves, player_bbs, opposition_bbs, en_passant_temp_idx
    )
    ordered_moves.extend([(move, False) for move in capture_moves])

    ordered_quiets = quiet_move_ordering(non_capture_moves, ply, side_idx)
    ordered_moves.extend([(move, True) for move in ordered_quiets])

    return ordered_moves, capture_moves


def quiet_move_ordering(quiet_moves, ply, side_idx):
    """
    Order all quiet moves, killer moves first followed by history moves
    """

    if ply >= MAX_PLY:
        return []

    killer1, killer2 = KILLER_MOVES[ply]
    ordered_quiets = []

    # Add killer moves
    for km in (killer1, killer2):
        if km is not None and km in quiet_moves and km not in ordered_quiets:
            ordered_quiets.append(km)

    # Sort the remaining history moves
    rest = [m for m in quiet_moves if m not in ordered_quiets]
    rest.sort(key=lambda m: HISTORY[side_idx][m[0]][m[1]], reverse=True)
    ordered_quiets.extend(rest)

    return ordered_quiets


# @profiled()
def can_do_lmr(state, move, depth, in_check, capture_moves, ply):
    """
    Check if the provided conditions allow for LMR to be applied

    Don't perform LMR on:
    - Captures and promotions
    - Moves while in check
    - Moves which give check
    - Killer moves
    - Depth is too low (depth < 3)
    """

    if depth < 3 or in_check:
        return False

    _, _, promotion = move
    if promotion is not None or move in capture_moves:
        return False

    if move in KILLER_MOVES[ply]:
        return False

    if move_gives_check(
        move,
        state.player_bbs,
        state.opposition_bbs,
        state.is_whites_move,
        state.en_passant_temp_idx,
        state.en_passant_real_idx,
    ):
        return False

    return True


# @profiled(root_only=True)
def quiescence_search(
    state: SearchState,
    legal_moves,
    alpha,
    beta,
    qdepth=6,
    ply=0,
    deadline=None,
):
    """
    Perform a quiescence search on the provided position
    """
    bump_node("q")

    def _quiesce_child(moves, best_value, alpha, beta):
        for move in moves:
            undo = make_move_inplace(state, move)

            new_legal_moves = find_legal_moves(
                state.player_bbs,
                state.opposition_bbs,
                state.is_whites_move,
                state.castling_rights,
                state.en_passant_temp_idx,
                state.en_passant_real_idx,
            )

            score, completed = quiescence_search(
                state,
                new_legal_moves,
                -beta,
                -alpha,
                qdepth - 1,
                ply + 1,
                deadline,
            )
            score = -score

            unmake_move_inplace(state, undo)

            if not completed:
                return 0, False

            if score >= beta:
                return score, True
            if score > best_value:
                best_value = score
            if score > alpha:
                alpha = score

        return best_value, True

    if deadline is not None and time.monotonic() >= deadline:
        return 0, False

    # No legal moves, so a mate has occurred
    king_square = state.player_bbs[5].bit_length() - 1
    in_check = is_square_attacked(
        king_square, state.opposition_bbs, state.player_bbs, not state.is_whites_move
    )

    if not legal_moves:
        if in_check:
            return -CHECKMATE_VALUE + ply, True

        return 0, True  # stalemate

    static_evaluation = static_eval(state.player_bbs, state.opposition_bbs, state.is_whites_move)
    best_value = static_evaluation

    # Ensure player is not in check as you cannot stand pat in such case
    if in_check:
        # Search the "best" evading move first
        capture_moves, non_capture_moves = mvv_lva_ordering(
            legal_moves, state.player_bbs, state.opposition_bbs, state.en_passant_temp_idx
        )

        # Keep searching if king is in check - ignore qdepth here
        # Set best_value to -infinity as that ensures best score comes from an evasion move, not static eval
        best_value = -math.inf
        return _quiesce_child(capture_moves + non_capture_moves, best_value, alpha, beta)

    if qdepth <= 0:
        return best_value, True

    # Stand pat - Assume at least one move can either match or beat the lower bound score
    # Based on Null Move Observation - assumes we are not in Zugzwang
    if best_value >= beta:
        return best_value, True  # fail-soft
    if best_value > alpha:
        alpha = best_value

    capture_moves, _ = mvv_lva_ordering(
        legal_moves, state.player_bbs, state.opposition_bbs, state.en_passant_temp_idx
    )

    return _quiesce_child(capture_moves, best_value, alpha, beta)


# @profiled(root_only=True)
def negamax(
    state: SearchState,
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
    bump_node("negamax")

    def _search_child(move, child_alpha, child_beta, child_depth):
        pre_state = ZobristState(
            state.is_whites_move,
            state.castling_rights,
            state.en_passant_temp_idx,
            state.player_bbs[0],
        )

        undo = make_move_inplace(state, move)

        post_state = ZobristState(
            state.is_whites_move,
            state.castling_rights,
            state.en_passant_temp_idx,
            state.player_bbs[0],
            undo.moved_piece_idx,
            undo.captured_piece_idx,
            undo.captured_piece_square,
        )

        child_key = update_key(zkey, move, pre_state, post_state)

        child_score, _, completed = negamax(
            state,
            child_alpha,
            child_beta,
            child_key,
            ply + 1,
            child_depth,
            None,
            deadline,
        )

        unmake_move_inplace(state, undo)

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

            TT[zkey] = TTEntry(zkey, move, depth, tt_score, node_type, state.halfmove_clock)

    if deadline is not None and time.monotonic() >= deadline:
        return 0, (), False

    if draw_by_insufficient_material(state.player_bbs, state.opposition_bbs):
        return 0, (), True

    # Draw by 50-move rule
    if state.halfmove_clock >= 100:
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
        state.player_bbs,
        state.opposition_bbs,
        state.is_whites_move,
        state.castling_rights,
        state.en_passant_temp_idx,
        state.en_passant_real_idx,
    )

    # No legal moves, so a mate has occurred
    king_square = state.player_bbs[5].bit_length() - 1
    in_check = is_square_attacked(
        king_square, state.opposition_bbs, state.player_bbs, not state.is_whites_move
    )
    if not legal_moves:
        if in_check:
            return -CHECKMATE_VALUE + ply, (), True

        return 0, (), True  # stalemate

    if depth <= 0:
        q_score, q_completed = quiescence_search(
            state,
            legal_moves,
            alpha,
            beta,
            ply=ply,
            deadline=deadline,
        )
        if q_completed:
            return q_score, (), True
        else:
            return 0, (), False

    best_move = ()
    best_score = -math.inf

    side_idx = history_side_idx(state.is_whites_move)
    ordered_moves, capture_moves = order_moves(
        legal_moves[:],
        state.player_bbs,
        state.opposition_bbs,
        state.en_passant_temp_idx,
        pv_move,
        entry,
        side_idx,
        ply,
    )

    for idx, (move, is_quiet_move) in enumerate(ordered_moves):
        # The PV move always gets searched at full depth
        if idx == 0:
            score, completed = _search_child(move, -beta, -alpha, depth - 1)
        else:
            if can_do_lmr(state, move, depth, in_check, capture_moves, ply):
                # Calculate search depth reduction
                reduction = 1
                if idx > 12:
                    reduction = 2  # Reduce more the further down the move list you get

                # Reduced depth search using null window
                score, completed = _search_child(move, -(alpha + 1), -alpha, depth - 1 - reduction)

                # If reduced search beats alpha we may have missed something
                do_full_depth_search = score > alpha
            else:
                do_full_depth_search = True

            # Full depth search using null window
            if do_full_depth_search:
                score, completed = _search_child(move, -(alpha + 1), -alpha, depth - 1)

            # Full depth search using full window
            if alpha < score < beta:
                score, completed = _search_child(move, -beta, -alpha, depth - 1)

        if not completed:
            return best_score, best_move, False

        if score > best_score:
            best_score = score
            best_move = move

            if score > alpha:
                alpha = score

        if score >= beta:
            if is_quiet_move:
                store_killer_move(ply, move)
                add_history(move, depth, side_idx)
            _store_tt(best_score, best_move, LOWER)
            return best_score, best_move, True

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
    depth=5,
    deadline=None,
    profiler=None,
):
    """
    Returns an evaluation of the the specified board position from the
    point of view of white, as well as the best move
    """
    global KILLER_MOVES

    player_bbs = white_bbs if is_whites_move else black_bbs
    opposition_bbs = black_bbs if is_whites_move else white_bbs

    best_move = ()
    best_eval = 0
    KILLER_MOVES = [[None, None] for _ in range(MAX_PLY)]
    decay_history()

    max_depth = 0

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
        )
        if book_move in legal_moves:
            return 0, book_move, 0

    # Compute zobrist key for current position
    zkey = compute_polyglot_key(
        white_bbs, black_bbs, castling_rights, en_passant_temp_idx, is_whites_move
    )

    state = SearchState(
        player_bbs,
        opposition_bbs,
        is_whites_move,
        castling_rights,
        en_passant_temp_idx,
        en_passant_real_idx,
        halfmove_clock,
    )

    for d in range(1, depth + 1):
        if deadline and time.monotonic() >= deadline:
            break

        profiler_context = active_profiler(profiler) if profiler is not None else nullcontext()
        with profiler_context:
            eval_d, move_d, completed_d = negamax(
                state,
                alpha=-math.inf,
                beta=math.inf,
                zkey=zkey,
                depth=d,
                pv_move=best_move,
                deadline=deadline,
            )

        if not completed_d:
            break

        max_depth = d

        if move_d:
            best_eval, best_move = eval_d, move_d
        else:
            break

    true_eval = best_eval if is_whites_move else -best_eval
    return true_eval, best_move, max_depth
