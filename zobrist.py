from polyglot_random import RANDOM64
from gamestate import WK, WQ, BK, BQ

# piece encodings relative to bitboard index
kind_of_piece_white = [1, 3, 5, 7, 9, 11]
kind_of_piece_black = [0, 2, 4, 6, 8, 10]


def polyglot_ep_file_to_xor(player_pawns_bb, ep_square, is_whites_move):
    """
    Check if an en passant capturing move exists regardless of if it's legal or not
    """

    if ep_square < 0:
        return None

    ep_file = ep_square & 7

    if is_whites_move:
        if ep_file > 0 and (player_pawns_bb & (1 << (ep_square - 9))):
            return ep_file
        if ep_file < 7 and (player_pawns_bb & (1 << (ep_square - 7))):
            return ep_file
    else:
        if ep_file > 0 and (player_pawns_bb & (1 << (ep_square + 7))):
            return ep_file
        if ep_file < 7 and (player_pawns_bb & (1 << (ep_square + 9))):
            return ep_file

    return None


def compute_polyglot_key(white_bbs, black_bbs, castling_rights, en_passant_idx, is_whites_move):
    """
    Compute the polyglot key for the polyglot opening book using RANDOM64
    """

    key = 0

    # piece xors
    for idx, bb in enumerate(white_bbs):
        while bb:
            lsb = bb & -bb
            square = lsb.bit_length() - 1

            offset_piece = 64 * kind_of_piece_white[idx] + square
            key ^= RANDOM64[offset_piece]

            bb ^= lsb
    for idx, bb in enumerate(black_bbs):
        while bb:
            lsb = bb & -bb
            square = lsb.bit_length() - 1

            offset_piece = 64 * kind_of_piece_black[idx] + square
            key ^= RANDOM64[offset_piece]

            bb ^= lsb

    # castling xors
    if castling_rights & WK:
        key ^= RANDOM64[768]
    if castling_rights & WQ:
        key ^= RANDOM64[769]
    if castling_rights & BK:
        key ^= RANDOM64[770]
    if castling_rights & BQ:
        key ^= RANDOM64[771]

    # en passant xor
    players_pawns_bb = white_bbs[0] if is_whites_move else black_bbs[0]
    ep_file = polyglot_ep_file_to_xor(players_pawns_bb, en_passant_idx, is_whites_move)
    if ep_file is not None:
        key ^= RANDOM64[772 + ep_file]

    # turn xor
    if is_whites_move:
        key ^= RANDOM64[780]

    return key
