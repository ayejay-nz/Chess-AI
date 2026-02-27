from dataclasses import dataclass

from polyglot_random import RANDOM64
from gamestate import WK, WQ, BK, BQ
from utils import piece_to_bitboard_index

# piece encodings relative to bitboard index
kind_of_piece_white = [1, 3, 5, 7, 9, 11]
kind_of_piece_black = [0, 2, 4, 6, 8, 10]


@dataclass(slots=True)
class ZobristState:
    is_whites_move: bool
    castling_rights: int
    en_passant_temp_idx: int
    player_pawn_bb: int
    moving_piece_idx: int | None = None
    captured_piece_idx: int | None = None
    captured_square_idx: int | None = None


def xor_castling_rights_mask(castling_rights, key):
    """
    Helper function to update a keys castling rights
    """

    if castling_rights & WK:
        key ^= RANDOM64[768]
    if castling_rights & WQ:
        key ^= RANDOM64[769]
    if castling_rights & BK:
        key ^= RANDOM64[770]
    if castling_rights & BQ:
        key ^= RANDOM64[771]

    return key


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
    key = xor_castling_rights_mask(castling_rights, key)

    # en passant xor
    players_pawns_bb = white_bbs[0] if is_whites_move else black_bbs[0]
    ep_file = polyglot_ep_file_to_xor(players_pawns_bb, en_passant_idx, is_whites_move)
    if ep_file is not None:
        key ^= RANDOM64[772 + ep_file]

    # turn xor
    if is_whites_move:
        key ^= RANDOM64[780]

    return key


def update_key(key, move, pre_state, post_state):
    """
    Update the zobrist key using simple XOR operations instead of recomputing it
    """

    pre_is_whites_move = pre_state.is_whites_move
    post_is_whites_move = post_state.is_whites_move

    # Calculate bit offset for moved piece
    kind_of_piece = kind_of_piece_white if pre_is_whites_move else kind_of_piece_black
    piece_idx = post_state.moving_piece_idx
    piece_offset = 64 * kind_of_piece[piece_idx]

    start_sq, end_sq, promo = move
    piece_start_offset = piece_offset + start_sq

    # xor correct bits if move is a promotion move
    if promo is not None:
        promo_idx = piece_to_bitboard_index(promo)
        piece_offset = 64 * kind_of_piece[promo_idx]

    piece_end_offset = piece_offset + end_sq

    # Update key for moved piece
    key ^= RANDOM64[piece_start_offset]
    key ^= RANDOM64[piece_end_offset]

    # Update rook if move is a castling move
    move_delta = end_sq - start_sq
    if abs(move_delta) == 2 and piece_idx == 5:
        is_kingside_castle = move_delta == 2
        if is_kingside_castle:
            rook_start_idx = start_sq + 3
            rook_end_idx = end_sq - 1
        else:
            rook_start_idx = start_sq - 4
            rook_end_idx = end_sq + 1

        # Update rook position
        rook_base_offset = 64 * kind_of_piece[3]
        key ^= RANDOM64[rook_base_offset + rook_start_idx]
        key ^= RANDOM64[rook_base_offset + rook_end_idx]

    # Update key for captured piece (if exists)
    if post_state.captured_piece_idx is not None:
        kind_of_piece_captured = kind_of_piece_black if pre_is_whites_move else kind_of_piece_white
        captured_idx = post_state.captured_piece_idx
        captured_base_offset = 64 * kind_of_piece_captured[captured_idx]

        # xor away captured piece
        key ^= RANDOM64[captured_base_offset + post_state.captured_square_idx]

    # Update key for castling rights
    castling_rights_delta = pre_state.castling_rights ^ post_state.castling_rights
    key = xor_castling_rights_mask(castling_rights_delta, key)

    # Update key for en passant
    pre_en_passant_temp_idx = pre_state.en_passant_temp_idx
    post_en_passant_temp_idx = post_state.en_passant_temp_idx

    pre_stm_pawn_bb = pre_state.player_pawn_bb
    post_stm_pawn_bb = post_state.player_pawn_bb

    pre_ep_file = polyglot_ep_file_to_xor(
        pre_stm_pawn_bb, pre_en_passant_temp_idx, pre_is_whites_move
    )
    post_ep_file = polyglot_ep_file_to_xor(
        post_stm_pawn_bb, post_en_passant_temp_idx, post_is_whites_move
    )

    # xor out old ep file, if it exists
    if pre_ep_file is not None:
        key ^= RANDOM64[772 + pre_ep_file]

    # xor in new ep file, if it exists
    if post_ep_file is not None:
        key ^= RANDOM64[772 + post_ep_file]

    # Update key for whos move it is
    key ^= RANDOM64[780]

    return key
