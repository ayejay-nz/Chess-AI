import gamestate
from moves import find_pseudo_legal_moves, in_check
from utils import get_file, get_rank


def game_over_status(
    player_bbs, opposition_bbs, is_users_move, is_whites_move, castling_rights, en_passant_temp_idx
):
    """
    Check whether the game has ended in a stalemate/checkmate

    Returns: -1 if computer won, 0 if stalemate, and 1 if user won
    """

    king_bb = player_bbs[5]
    king_square = king_bb.bit_length() - 1

    o_piece_captures, _, _, _ = find_pseudo_legal_moves(
        opposition_bbs,
        player_bbs,
        not is_whites_move,
        castling_rights,
        en_passant_temp_idx,
    )

    if in_check(king_square, o_piece_captures):
        return -1 if is_users_move else 1
    return 0


def is_white_square(square):
    """
    Check if a square provided its index is a white square or not
    """

    rank = get_rank(square)
    file = get_file(square)

    return (rank + file) % 2 == 1


def draw_by_insufficient_material(white_bbs, black_bbs):
    """
    Check if there is insufficient material to continue the game
    """

    white_knight_bb, black_knight_bb = white_bbs[2], black_bbs[2]
    white_bishop_bb, black_bishop_bb = white_bbs[3], black_bbs[3]

    # Sufficient material to continue
    if (
        white_bbs[0] | black_bbs[0] | white_bbs[1] | black_bbs[1] | white_bbs[4] | black_bbs[4]
    ) != 0:
        return False

    white_knights = white_knight_bb.bit_count()
    black_knights = black_knight_bb.bit_count()
    white_bishops = white_bishop_bb.bit_count()
    black_bishops = black_bishop_bb.bit_count()

    white_minors = white_knights + white_bishops
    black_minors = black_knights + black_bishops
    minor_pieces = white_minors + black_minors

    if minor_pieces == 0 or minor_pieces == 1:
        return True

    if minor_pieces > 2:
        return False

    # Two minor pieces left
    if white_bishops == 1 and black_bishops == 1:
        wb_square = (white_bishop_bb & -white_bishop_bb).bit_length() - 1
        bb_square = (black_bishop_bb & -black_bishop_bb).bit_length() - 1

        return not (is_white_square(wb_square) ^ is_white_square(bb_square))

    if white_bishops == 2 or black_bishops == 2:
        bishops_bb = white_bishop_bb if white_bishops == 2 else black_bishop_bb

        lsb1 = bishops_bb & -bishops_bb
        bishop1_square = lsb1.bit_length() - 1
        bishop1_is_white = is_white_square(bishop1_square)

        bishops_bb ^= lsb1
        lsb2 = bishops_bb & -bishops_bb
        bishop2_square = lsb2.bit_length() - 1
        bishop2_is_white = is_white_square(bishop2_square)

        return not (bishop1_is_white ^ bishop2_is_white)

    return False


def has_legal_ep_capture(pawn_bb, legal_moves, en_passant_temp_idx):
    """
    Check if a side has a legal en passant move
    """

    if en_passant_temp_idx == 0:
        return False

    ep_file = get_file(en_passant_temp_idx)
    for start_square, end_square, _ in legal_moves:
        if end_square != en_passant_temp_idx:
            continue
        if not (2**start_square & pawn_bb):
            continue
        if abs(get_file(start_square) - ep_file) == 1:
            return True

    return False


def position_key(white_bbs, black_bbs, is_whites_move, castling_rights, en_passant_temp_idx):
    """
    Generate a key of the current game position
    """

    return (
        tuple(white_bbs),
        tuple(black_bbs),
        is_whites_move,
        castling_rights,
        en_passant_temp_idx,
    )


def update_repetition_count(
    white_bbs, black_bbs, is_whites_move, castling_rights, en_passant_temp_idx, legal_moves
):
    """
    Update gamestate position_counts dictionary
    """

    side_pawn_bb = white_bbs[0] if is_whites_move else black_bbs[0]
    ep_key = (
        en_passant_temp_idx
        if has_legal_ep_capture(side_pawn_bb, legal_moves, en_passant_temp_idx)
        else 0
    )

    key = position_key(white_bbs, black_bbs, is_whites_move, castling_rights, ep_key)
    gamestate.position_counts[key] = gamestate.position_counts.get(key, 0) + 1
    return gamestate.position_counts[key] >= 3
