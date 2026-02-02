def rank_to_row(raw_row, rank):
    """
    Convert a singular row into a row given its rank 

    Example: raw_row = 255 (11111111), rank = 2 -> 65280 (1111111100000000)
    """

    return raw_row << (8 * (rank - 1))

def init_bitboards(white_is_bottom=True): 
    """
    Initialise bitboards for white and black, returning a tuple of the white and black bitboard array, in that order.

    bb1 = pawns, bb2 = rooks, bb3 = knight, bb4 = bishop, bb5 = queen, bb6 = king

    Bottom left of board is index 0, incrementing from left to right and up
    """

    pawns_row = 0b11111111
    rooks_row = 0b10000001
    knights_row = 0b01000010
    bishops_row = 0b00100100
    d_file_bit = 0b00010000
    e_file_bit = 0b00001000

    # Create bitboards for bottom player excluding king/queen
    bitboards_bottom = [rank_to_row(pawns_row, 2), rooks_row, knights_row, bishops_row]
    # Create bitboards for top player excluding king/queen
    bitboards_top = [rank_to_row(pawns_row, 7), rank_to_row(rooks_row, 8), rank_to_row(knights_row, 8), rank_to_row(bishops_row, 8)]

    if white_is_bottom:
        bitboards_bottom.extend([d_file_bit, e_file_bit])
        bitboards_top.extend([rank_to_row(d_file_bit, 8), rank_to_row(e_file_bit, 8)])
        return (bitboards_bottom, bitboards_top)
    else: 
        bitboards_bottom.extend([e_file_bit, d_file_bit])
        bitboards_top.extend([rank_to_row(e_file_bit, 8), rank_to_row(d_file_bit, 8)])
        return (bitboards_top, bitboards_bottom)

def user_wants_white():
    """
    Get what colour the user wants to play as
    """

    white_options = ['white', 'w']
    black_options = ['black', 'b']

    while True:
        response = input('Do you want to play as white or black? \n').lower()
        if response in white_options:
            return True
        elif response in black_options:
            return False

def output_boardstate(white_bbs, black_bbs):
    """
    Output the current boardstate from the white/black bitboards
    """

    white_piece_order = ['♙', '♖', '♘', '♗', '♕', '♔']
    black_piece_order = ['♟', '♜', '♞', '♝', '♛', '♚']
    board = ['.'] * 64

    for idx, bb in enumerate(white_bbs):
        piece = white_piece_order[idx]
        while bb:
            lsb = bb & -bb
            square = 64 - lsb.bit_length()
            board[square] = piece
            bb ^= lsb

    for idx, bb in enumerate(black_bbs):
        piece = black_piece_order[idx]
        while bb:
            lsb = bb & -bb
            square = 64 - lsb.bit_length()
            board[square] = piece
            bb ^= lsb

    lines = []
    for rank in range(7, -1, -1):
        row = board[rank * 8: (rank + 1) * 8]
        lines.append(str(rank + 1) + ' ' + ' '.join(row))
    lines.append('  a b c d e f g h')

    print('\n'.join(lines))

def main():
    is_white = user_wants_white()
    white_bbs, black_bbs = init_bitboards(is_white)
    output_boardstate(white_bbs, black_bbs)

if __name__ == '__main__':
    main()
