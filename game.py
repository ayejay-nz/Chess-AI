from moves import find_pseudo_legal_moves, in_check


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
