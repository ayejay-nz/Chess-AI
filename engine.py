PIECE_VALUES = {
    0: 100,  # pawn
    1: 500,  # rook
    2: 320,  # knight
    3: 330,  # bishop
    4: 900,  # queen
}


def evaluate_position(white_bbs, black_bbs, is_whites_move):
    """
    Returns an evaluation of the the specified board position from the
    point of view of the side to move
    """

    white_based_eval = 0

    for idx, bb in enumerate(white_bbs):
        piece_count = bb.bit_count()
        white_based_eval += piece_count * PIECE_VALUES.get(idx, 0)

    for idx, bb in enumerate(black_bbs):
        piece_count = bb.bit_count()
        black_based_eval -= piece_count * PIECE_VALUES.get(idx, 0)

    return white_based_eval if is_whites_move else -white_based_eval
