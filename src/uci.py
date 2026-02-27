import sys
import time
import inspect
from dataclasses import dataclass

from engine import evaluate_position
from gamestate import BK, BQ, WK, WQ
from moves import apply_move, find_legal_moves, find_pseudo_legal_moves, in_check

# Canonical chess start position (used for uci `position startpos`)
START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
PIECE_TO_INDEX = {
    "p": 0,
    "n": 1,
    "b": 2,
    "r": 3,
    "q": 4,
    "k": 5,
}


def resolve_engine_default_depth() -> int:
    try:
        depth_default = inspect.signature(evaluate_position).parameters["depth"].default
    except (TypeError, ValueError, KeyError):
        return 3

    if isinstance(depth_default, int) and depth_default > 0:
        return depth_default
    return 3


DEFAULT_UCI_DEPTH = resolve_engine_default_depth()
MIN_CLOCK_BUDGET_MS = 10.0
ESTIMATED_MOVES_TO_GO = 35.0
INCREMENT_USAGE = 0.8
MAX_CLOCK_SHARE = 0.08
EMERGENCY_CLOCK_MS = 2_000
EMERGENCY_CLOCK_SHARE = 0.20


@dataclass(frozen=True)
class Position:
    white_bbs: list[int]
    black_bbs: list[int]
    is_whites_move: bool
    castling_rights: int
    en_passant_temp_idx: int
    en_passant_real_idx: int
    halfmove_clock: int
    fullmove_number: int


def square_to_index(square: str) -> int:
    file_idx = ord(square[0]) - ord("a")
    rank_idx = int(square[1]) - 1
    return rank_idx * 8 + file_idx


def index_to_square(index: int) -> str:
    file_ch = chr(ord("a") + (index % 8))
    rank_ch = str(index // 8 + 1)
    return file_ch + rank_ch


def move_to_uci(move: tuple[int, int, str | None]) -> str:
    start_square, end_square, promotion_piece = move
    promotion_suffix = promotion_piece if promotion_piece else ""
    return index_to_square(start_square) + index_to_square(end_square) + promotion_suffix


def parse_uci_move(move_text: str) -> tuple[int, int, str | None] | None:
    if len(move_text) not in (4, 5):
        return None

    start_square = move_text[:2]
    end_square = move_text[2:4]

    if not (
        "a" <= start_square[0] <= "h"
        and "1" <= start_square[1] <= "8"
        and "a" <= end_square[0] <= "h"
        and "1" <= end_square[1] <= "8"
    ):
        return None

    start_idx = square_to_index(start_square)
    end_idx = square_to_index(end_square)
    promotion_piece = None

    if len(move_text) == 5:
        promotion_piece = move_text[4].lower()
        if promotion_piece not in ("q", "r", "b", "n"):
            return None

    return start_idx, end_idx, promotion_piece


def parse_fen(fen: str) -> Position:
    fields = fen.strip().split()
    if len(fields) < 4:
        raise ValueError("FEN must contain at least 4 space-separated fields")

    board_field, side_field, castling_field, ep_field = fields[:4]
    halfmove_clock = int(fields[4]) if len(fields) >= 5 else 0
    fullmove_number = int(fields[5]) if len(fields) >= 6 else 1

    ranks = board_field.split("/")
    if len(ranks) != 8:
        raise ValueError("FEN board field must contain 8 ranks")

    white_bbs = [0] * 6
    black_bbs = [0] * 6

    for fen_rank_idx, rank_str in enumerate(ranks):
        board_rank = 7 - fen_rank_idx
        file_idx = 0

        for ch in rank_str:
            if ch.isdigit():
                file_idx += int(ch)
                continue

            if ch.lower() not in PIECE_TO_INDEX:
                raise ValueError("Unknown piece in FEN board field")
            if file_idx >= 8:
                raise ValueError("Too many squares in FEN rank")

            square_idx = board_rank * 8 + file_idx
            piece_idx = PIECE_TO_INDEX[ch.lower()]
            bit = 1 << square_idx

            if ch.isupper():
                white_bbs[piece_idx] |= bit
            else:
                black_bbs[piece_idx] |= bit

            file_idx += 1

        if file_idx != 8:
            raise ValueError("FEN rank does not contain exactly 8 squares")

    is_whites_move = side_field == "w"

    castling_rights = 0
    if "K" in castling_field:
        castling_rights |= WK
    if "Q" in castling_field:
        castling_rights |= WQ
    if "k" in castling_field:
        castling_rights |= BK
    if "q" in castling_field:
        castling_rights |= BQ

    en_passant_temp_idx = -1
    en_passant_real_idx = -1
    if ep_field != "-":
        en_passant_temp_idx = square_to_index(ep_field)
        # If white is to move, black just advanced 2 squares (capturable pawn is one rank below target).
        if is_whites_move:
            en_passant_real_idx = en_passant_temp_idx - 8
        else:
            en_passant_real_idx = en_passant_temp_idx + 8

        if en_passant_real_idx < 0 or en_passant_real_idx > 63:
            en_passant_temp_idx = -1
            en_passant_real_idx = -1

    return Position(
        white_bbs=white_bbs,
        black_bbs=black_bbs,
        is_whites_move=is_whites_move,
        castling_rights=castling_rights,
        en_passant_temp_idx=en_passant_temp_idx,
        en_passant_real_idx=en_passant_real_idx,
        halfmove_clock=halfmove_clock,
        fullmove_number=fullmove_number,
    )


def initial_position() -> Position:
    return parse_fen(START_FEN)


def get_side_bitboards(position: Position) -> tuple[list[int], list[int]]:
    if position.is_whites_move:
        return position.white_bbs, position.black_bbs
    return position.black_bbs, position.white_bbs


def generate_legal_moves(position: Position) -> list[tuple[int, int, str | None]]:
    player_bbs, opposition_bbs = get_side_bitboards(position)
    return find_legal_moves(
        player_bbs,
        opposition_bbs,
        position.is_whites_move,
        position.castling_rights,
        position.en_passant_temp_idx,
        position.en_passant_real_idx,
    )


def is_side_to_move_in_check(position: Position) -> bool:
    player_bbs, opposition_bbs = get_side_bitboards(position)

    king_bb = player_bbs[5]
    if king_bb == 0:
        return False

    king_square = king_bb.bit_length() - 1
    opposition_piece_moves, opposition_king_moves, _, _ = find_pseudo_legal_moves(
        opposition_bbs,
        player_bbs,
        not position.is_whites_move,
        position.castling_rights,
        position.en_passant_temp_idx,
    )

    return in_check(king_square, opposition_piece_moves + opposition_king_moves)


def make_move(position: Position, move: tuple[int, int, str | None]) -> Position:
    player_bbs, opposition_bbs = get_side_bitboards(position)

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
        position.en_passant_temp_idx,
        position.en_passant_real_idx,
        position.halfmove_clock,
        position.castling_rights,
        position.is_whites_move,
    )

    if position.is_whites_move:
        next_white_bbs = new_player_bbs
        next_black_bbs = new_opposition_bbs
        next_fullmove = position.fullmove_number
    else:
        next_white_bbs = new_opposition_bbs
        next_black_bbs = new_player_bbs
        next_fullmove = position.fullmove_number + 1

    return Position(
        white_bbs=next_white_bbs,
        black_bbs=next_black_bbs,
        is_whites_move=not position.is_whites_move,
        castling_rights=new_castling_rights,
        en_passant_temp_idx=new_en_passant_temp_idx,
        en_passant_real_idx=new_en_passant_real_idx,
        halfmove_clock=new_halfmove_clock,
        fullmove_number=next_fullmove,
    )


def parse_go_args(command: str, is_whites_move: bool) -> tuple[int, float | None]:
    tokens = command.split()

    depth = None
    has_explicit_depth = False
    movetime_ms = None
    wtime_ms = None
    btime_ms = None
    winc_ms = 0
    binc_ms = 0

    i = 1
    while i < len(tokens):
        token = tokens[i]

        def read_int(default=None):
            if i + 1 >= len(tokens):
                return default
            try:
                return int(tokens[i + 1])
            except ValueError:
                return default

        if token == "depth":
            depth = read_int(depth)
            has_explicit_depth = True
            i += 2
            continue
        if token == "movetime":
            movetime_ms = read_int(movetime_ms)
            i += 2
            continue
        if token == "wtime":
            wtime_ms = read_int(wtime_ms)
            i += 2
            continue
        if token == "btime":
            btime_ms = read_int(btime_ms)
            i += 2
            continue
        if token == "winc":
            winc_ms = read_int(winc_ms)
            i += 2
            continue
        if token == "binc":
            binc_ms = read_int(binc_ms)
            i += 2
            continue

        i += 1

    if depth is None or depth <= 0:
        depth = DEFAULT_UCI_DEPTH

    time_limit_s = None
    if movetime_ms is not None:
        # Avoid immediate root timeout for `movetime 0` and tiny values.
        time_limit_s = max(0.01, movetime_ms / 1000.0)
    elif not has_explicit_depth and wtime_ms is not None and btime_ms is not None:
        remaining_ms = max(0, wtime_ms if is_whites_move else btime_ms)
        increment_ms = max(0, winc_ms if is_whites_move else binc_ms)

        base_ms = remaining_ms / ESTIMATED_MOVES_TO_GO
        alloc_ms = base_ms + increment_ms * INCREMENT_USAGE

        clock_share = MAX_CLOCK_SHARE
        if remaining_ms <= EMERGENCY_CLOCK_MS:
            clock_share = EMERGENCY_CLOCK_SHARE

        alloc_ms = min(alloc_ms, remaining_ms * clock_share)
        alloc_ms = min(alloc_ms, remaining_ms * 0.9) if remaining_ms > 0 else MIN_CLOCK_BUDGET_MS
        alloc_ms = max(MIN_CLOCK_BUDGET_MS, alloc_ms)
        time_limit_s = alloc_ms / 1000.0

    return depth, time_limit_s


def search_best_move(
    position: Position,
    go_command: str,
    position_counts: dict,
) -> tuple[int, int, str | None] | None:
    legal_moves = generate_legal_moves(position)
    if not legal_moves:
        return None

    search_depth, time_limit_s = parse_go_args(go_command, position.is_whites_move)
    deadline = None if time_limit_s is None else time.monotonic() + time_limit_s

    best_eval, best_move = evaluate_position(
        position.white_bbs,
        position.black_bbs,
        position.is_whites_move,
        position.en_passant_temp_idx,
        position.en_passant_real_idx,
        position.castling_rights,
        position.halfmove_clock,
        depth=search_depth,
        deadline=deadline,
    )

    if not best_move:
        # Always return a move immediately under time pressure.
        best_move = legal_moves[0]
        best_eval = 0.0

    cp_score = int(best_eval if position.is_whites_move else -best_eval)
    print(f"info depth {search_depth} score cp {cp_score} pv {move_to_uci(best_move)}", flush=True)

    return best_move


def apply_moves_text(position: Position, moves_text: list[str]) -> Position:
    current = position

    for move_text in moves_text:
        parsed = parse_uci_move(move_text)
        if parsed is None:
            break

        legal_moves = generate_legal_moves(current)
        move = None

        for legal in legal_moves:
            if legal == parsed:
                move = legal
                break

            # Accept long algebraic promotion piece in upper-case from some GUIs.
            if (
                legal[0] == parsed[0]
                and legal[1] == parsed[1]
                and legal[2] is not None
                and parsed[2] is not None
                and legal[2].lower() == parsed[2].lower()
            ):
                move = legal
                break

        if move is None:
            break

        current = make_move(current, move)

    return current


def parse_position_command(command: str) -> Position:
    # UCI form:
    # position startpos [moves ...]
    # position fen <fen-string> [moves ...]

    if not command.startswith("position "):
        return initial_position()

    payload = command[len("position ") :].strip()
    if payload.startswith("startpos"):
        position = initial_position()
        rest = payload[len("startpos") :].strip()

        if rest.startswith("moves"):
            move_tokens = rest[len("moves") :].strip().split()
            position = apply_moves_text(position, move_tokens)

        return position

    if payload.startswith("fen "):
        fen_and_moves = payload[len("fen ") :]
        if " moves " in fen_and_moves:
            fen_text, moves_text = fen_and_moves.split(" moves ", 1)
            move_tokens = moves_text.strip().split()
        else:
            fen_text = fen_and_moves
            move_tokens = []

        position = parse_fen(fen_text.strip())
        position = apply_moves_text(position, move_tokens)
        return position

    return initial_position()


def uci_loop() -> None:
    position = initial_position()
    position_counts = {}

    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue

        if line == "uci":
            print("id name Chess-AI", flush=True)
            print("id author ayejay", flush=True)
            print("uciok", flush=True)
            continue

        if line == "isready":
            print("readyok", flush=True)
            continue

        if line == "ucinewgame":
            position = initial_position()
            position_counts = {}
            continue

        if line.startswith("position "):
            try:
                position = parse_position_command(line)
                position_counts = {}
            except Exception:
                # Ignore malformed positions to keep loop alive.
                position = initial_position()
                position_counts = {}
            continue

        if line.startswith("go"):
            best_move = search_best_move(position, line, position_counts)
            if best_move is None:
                print("bestmove 0000", flush=True)
            else:
                print(f"bestmove {move_to_uci(best_move)}", flush=True)
            continue

        if line == "stop":
            # Search is synchronous right now; this is a no-op.
            continue

        if line == "quit":
            return

        if line == "ponderhit":
            continue

        # Ignore unsupported commands, including setoption.


if __name__ == "__main__":
    uci_loop()
