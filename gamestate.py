is_whites_move = True
is_playing_white = True

WK, WQ, BK, BQ = 1, 2, 4, 8
castling_rights = WK | WQ | BK | BQ

def output_boardstate(white_bbs, black_bbs, is_white):
    """
    Output the current boardstate from the white/black bitboards
    """

    black_piece_order = ['♙', '♖', '♘', '♗', '♕', '♔']
    white_piece_order = ['♟', '♜', '♞', '♝', '♛', '♚']
    board = ['.'] * 64

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
    for rank in range(7, -1, -1):
        row = board[rank * 8: (rank + 1) * 8]
        
        if is_white: lines.append(str(rank + 1) + ' ' + ' '.join(row))
        else: lines.append(str(8 - rank) + ' ' + ' '.join(row))
        
    if is_white: lines.append('  a b c d e f g h')
    else: lines.append('  h g f e d c b a')

    print('\n'.join(lines))
