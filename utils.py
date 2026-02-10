import gamestate
from gamestate import PLAYER_ON_BOTTOM


def output_boardstate(white_bbs, black_bbs):
    """
    Output the current boardstate from the white/black bitboards
    """

    black_piece_order = ["♙", "♖", "♘", "♗", "♕", "♔"]
    white_piece_order = ["♟", "♜", "♞", "♝", "♛", "♚"]
    board = ["."] * 64

    for idx, bb in enumerate(white_bbs):
        piece = white_piece_order[idx]
        while bb:
            lsb = bb & -bb
            square = lsb.bit_length() - 1
            board[square] = piece
            bb ^= lsb

    for idx, bb in enumerate(black_bbs):
        piece = black_piece_order[idx]
        while bb:
            lsb = bb & -bb
            square = lsb.bit_length() - 1
            board[square] = piece
            bb ^= lsb

    lines = []
    for rank_idx in range(7, -1, -1):
        # Board is "mirrored" if playing as black and on the bottom
        mirrored_board = PLAYER_ON_BOTTOM and not gamestate.is_playing_white

        base = rank_idx if not mirrored_board else 7 - rank_idx
        rank = board[base * 8 : (base + 1) * 8]
        if mirrored_board:
            rank.reverse()

        lines.append(str(base + 1) + " " + " ".join(rank))

    if not mirrored_board:
        lines.append("  a b c d e f g h")
    else:
        lines.append("  h g f e d c b a")

    print("\n".join(lines))
